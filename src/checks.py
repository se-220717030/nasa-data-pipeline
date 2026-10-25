"""Six database checks, run on a temporary copy of data/asteroids.db (never the real one).

Run from the repository root, after src/load.py:
    python src/checks.py

Every check has two parts:
  * scan  - the loaded data really has no violations;
  * probe - the database itself refuses a deliberately bad write
            (so the guarantee comes from the schema, not from luck).
Exit code is 0 only if all six checks PASS.
"""
import contextlib
import gc
import io
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

from db import DB_PATH, connect
from load import RAW, load


def opened(path):
    """connect() that is really closed after the with-block (needed on Windows)."""
    return contextlib.closing(connect(path))

TABLES = ("asteroids", "orbits", "approaches", "quarantine")


def counts(con):
    # Table names come from the fixed tuple above, not from user data
    return {t: con.execute("SELECT COUNT(*) FROM " + t).fetchone()[0] for t in TABLES}


def snapshot(con):
    """Row counts plus a full content fingerprint of the entity tables."""
    snap = counts(con)
    snap["asteroids_rows"] = con.execute(
        "SELECT * FROM asteroids ORDER BY asteroid_key").fetchall()
    snap["orbits_rows"] = con.execute(
        "SELECT * FROM orbits ORDER BY orbit_key").fetchall()
    snap["approaches_sum"] = con.execute(
        "SELECT COUNT(*), SUM(asteroid_key), SUM(epoch_date_close_approach), "
        "TOTAL(miss_distance_km), TOTAL(relative_velocity_km_s) FROM approaches").fetchone()
    return snap


def rejected(con, sql, params=()):
    """True if SQLite refuses the write. Nothing is kept either way."""
    try:
        con.execute("SAVEPOINT probe")
        con.execute(sql, params)
        return False
    except sqlite3.IntegrityError:
        return True
    finally:
        con.execute("ROLLBACK TO probe")
        con.execute("RELEASE probe")


def quiet_load(db_path, raw_dir=RAW):
    with contextlib.redirect_stdout(io.StringIO()):
        return load(db_path, raw_dir)


# ---------------------------------------------------------------- the six checks

def check_duplicate_key(con):
    dup_ast = con.execute(
        "SELECT COUNT(*) FROM (SELECT source_id FROM asteroids GROUP BY source_id HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    dup_orb = con.execute(
        "SELECT COUNT(*) FROM (SELECT asteroid_key FROM orbits GROUP BY asteroid_key HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    dup_app = con.execute(
        "SELECT COUNT(*) FROM (SELECT asteroid_key, epoch_date_close_approach, orbiting_body "
        "FROM approaches GROUP BY asteroid_key, epoch_date_close_approach, orbiting_body "
        "HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    a = con.execute("SELECT * FROM approaches LIMIT 1").fetchone()
    sid = con.execute("SELECT source_id FROM asteroids LIMIT 1").fetchone()[0]
    probe = (
        rejected(con, "INSERT INTO asteroids (source_id, retrieved_at) VALUES (?, 'x')", (sid,))
        and rejected(con, "INSERT INTO approaches (asteroid_key, epoch_date_close_approach, "
                          "close_approach_date, orbiting_body, retrieved_at) "
                          "VALUES (?, ?, '2000-01-01', ?, 'x')", (a[0], a[1], a[6]))
    )
    ok = dup_ast == dup_orb == dup_app == 0 and probe
    return ok, (f"duplicates: asteroids={dup_ast}, orbits={dup_orb}, approaches={dup_app}; "
                f"duplicate insert rejected: {probe}")


def check_orphan_event(con):
    fk = con.execute("PRAGMA foreign_key_check").fetchall()
    orphans = con.execute(
        "SELECT (SELECT COUNT(*) FROM approaches p LEFT JOIN asteroids a USING (asteroid_key) "
        "        WHERE a.asteroid_key IS NULL) + "
        "       (SELECT COUNT(*) FROM orbits o LEFT JOIN asteroids a USING (asteroid_key) "
        "        WHERE a.asteroid_key IS NULL)"
    ).fetchone()[0]
    missing = con.execute("SELECT COALESCE(MAX(asteroid_key), 0) + 1000000 FROM asteroids").fetchone()[0]
    probe = rejected(
        con, "INSERT INTO approaches (asteroid_key, epoch_date_close_approach, close_approach_date, "
             "orbiting_body, retrieved_at) VALUES (?, 0, '2000-01-01', 'Earth', 'x')", (missing,))
    ok = not fk and orphans == 0 and probe
    return ok, f"foreign_key_check rows={len(fk)}, orphan rows={orphans}; orphan insert rejected: {probe}"


def check_null_key(con):
    nulls = con.execute(
        "SELECT (SELECT COUNT(*) FROM asteroids WHERE source_id IS NULL) + "
        "       (SELECT COUNT(*) FROM orbits WHERE source_id IS NULL OR asteroid_key IS NULL) + "
        "       (SELECT COUNT(*) FROM approaches WHERE asteroid_key IS NULL "
        "        OR epoch_date_close_approach IS NULL OR orbiting_body IS NULL)"
    ).fetchone()[0]
    k = con.execute("SELECT asteroid_key FROM asteroids LIMIT 1").fetchone()[0]
    probe = (
        rejected(con, "INSERT INTO asteroids (source_id, retrieved_at) VALUES (NULL, 'x')")
        and rejected(con, "INSERT INTO approaches (asteroid_key, epoch_date_close_approach, "
                          "close_approach_date, orbiting_body, retrieved_at) "
                          "VALUES (?, NULL, '2000-01-01', 'Earth', 'x')", (k,))
    )
    ok = nulls == 0 and probe
    return ok, f"NULL key values={nulls}; NULL key insert rejected: {probe}"


def check_wrong_type(con):
    # typeof() must match the declared type (or be null for optional columns)
    bad = con.execute(
        "SELECT "
        " (SELECT COUNT(*) FROM asteroids WHERE typeof(source_id) <> 'text' "
        "     OR typeof(absolute_magnitude_h) NOT IN ('real', 'null') "
        "     OR typeof(is_potentially_hazardous) NOT IN ('integer', 'null')) + "
        " (SELECT COUNT(*) FROM orbits WHERE typeof(eccentricity) NOT IN ('real', 'null') "
        "     OR typeof(inclination) NOT IN ('real', 'null')) + "
        " (SELECT COUNT(*) FROM approaches WHERE typeof(epoch_date_close_approach) <> 'integer' "
        "     OR typeof(miss_distance_km) NOT IN ('real', 'null') "
        "     OR typeof(relative_velocity_km_s) NOT IN ('real', 'null') "
        "     OR close_approach_date NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')"
    ).fetchone()[0]
    a = con.execute("SELECT asteroid_key FROM asteroids LIMIT 1").fetchone()[0]
    probe = (
        rejected(con, "INSERT INTO asteroids (source_id, absolute_magnitude_h, retrieved_at) "
                      "VALUES ('type-probe', 'very bright', 'x')")
        and rejected(con, "INSERT INTO approaches (asteroid_key, epoch_date_close_approach, "
                          "close_approach_date, orbiting_body, retrieved_at) "
                          "VALUES (?, 'yesterday', '2000-01-01', 'Earth', 'x')", (a,))
        and rejected(con, "INSERT INTO asteroids (source_id, is_potentially_hazardous, retrieved_at) "
                          "VALUES ('flag-probe', 7, 'x')")
    )
    ok = bad == 0 and probe
    return ok, f"rows with wrong type={bad}; text-in-number and bad flag rejected: {probe}"


def check_idempotence(db_copy):
    with opened(db_copy) as con:
        before = snapshot(con)
    quiet_load(db_copy)
    with opened(db_copy) as con:
        after = snapshot(con)
    ok = before == after
    c = counts_line(before)
    return ok, f"reloaded all raw files into the copy; before={c}, after={counts_line(after)}, identical={ok}"


def check_atomicity(workdir):
    # (a) a failure in the middle of writing must roll back everything already written
    db = workdir / "atomicity.db"
    with opened(db) as con:
        con.executescript(Path(RAW).parents[1].joinpath("sql", "schema.sql").read_text(encoding="utf-8"))
        con.execute("CREATE TRIGGER fail_mid_load BEFORE INSERT ON approaches "
                    "WHEN (SELECT COUNT(*) FROM approaches) >= 1000 "
                    "BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
        con.commit()
    failed_a = False
    try:
        quiet_load(db)
    except sqlite3.DatabaseError:
        failed_a = True
    with opened(db) as con:
        after_a = counts(con)
    a_ok = failed_a and all(v == 0 for v in after_a.values())

    # (b) a broken raw file must stop the run before anything is written
    raw_bad = workdir / "raw_bad"
    shutil.copytree(RAW, raw_bad)
    (raw_bad / "browse_20991231T000000Z_broken.json").write_text("{ not json", encoding="utf-8")
    db_b = workdir / "atomicity_b.db"
    failed_b = False
    try:
        quiet_load(db_b, raw_bad)
    except ValueError:  # json.JSONDecodeError is a ValueError
        failed_b = True
    with opened(db_b) as con:
        after_b = counts(con)
    b_ok = failed_b and all(v == 0 for v in after_b.values())

    return a_ok and b_ok, (f"failure after 1,000 approaches -> rows left={sum(after_a.values())}; "
                           f"broken JSON file -> rows left={sum(after_b.values())}")


def counts_line(c):
    return "/".join(f"{c[t]:,}" for t in TABLES)


def main():
    if not Path(DB_PATH).exists():
        sys.exit(f"{DB_PATH} not found - run python src/load.py first")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        tmp = Path(tmp)
        db_copy = tmp / "asteroids_copy.db"
        shutil.copy2(DB_PATH, db_copy)

        con = connect(db_copy)
        con.isolation_level = None  # autocommit; probes use explicit savepoints
        print(f"checks on a temporary copy of {Path(DB_PATH).name}: "
              f"asteroids/orbits/approaches/quarantine = {counts_line(counts(con))}")
        results = [
            ("1. duplicate natural key", *check_duplicate_key(con)),
            ("2. orphan event", *check_orphan_event(con)),
            ("3. NULL key", *check_null_key(con)),
            ("4. wrong type", *check_wrong_type(con)),
        ]
        con.close()
        results.append(("5. idempotence", *check_idempotence(db_copy)))
        results.append(("6. atomicity", *check_atomicity(tmp)))
        gc.collect()  # release the connection left by the deliberately failed load

    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name:<26} {detail}")
    passed = sum(ok for _, ok, _ in results)
    print(f"{passed}/{len(results)} checks passed")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
