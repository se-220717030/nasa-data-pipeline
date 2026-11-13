"""Helpers imported by notebooks/m4_eda.ipynb.

Read-only by design: every connection is opened with mode=ro, and db_fingerprint() lets the notebook
prove that the database file is byte-for-byte the same after it ran.
"""
import hashlib
import sqlite3
from pathlib import Path
from urllib.parse import quote

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "asteroids.db"
QUERIES = ROOT / "sql" / "queries"
FIGURES = ROOT / "figures"


def connect_ro(db_path=DB_PATH):
    """Read-only connection: exploration can never change the database."""
    return sqlite3.connect("file:" + quote(Path(db_path).as_posix()) + "?mode=ro", uri=True)


def db_fingerprint(db_path=DB_PATH):
    """SHA-256 of the database file. Equal before and after the notebook = nothing was written."""
    return hashlib.sha256(Path(db_path).read_bytes()).hexdigest()


def load_query(name):
    """SQL text of sql/queries/<name>.sql (queries are kept in files so M5/M7 can reuse them)."""
    return (QUERIES / f"{name}.sql").read_text(encoding="utf-8")


def query(con, sql, params=None):
    """Run a query; every value goes through a placeholder."""
    return pd.read_sql_query(sql, con, params=params or {})


def ecdf(values):
    """Sorted values and their cumulative share, for an ECDF step plot."""
    x = np.sort(np.asarray(values, dtype=float))
    return x, np.arange(1, len(x) + 1) / len(x)


def bootstrap_ci(a, b, stat=np.median, n_boot=2000, seed=0, level=0.95):
    """Percentile bootstrap interval for stat(a) - stat(b); a and b are per-unit values (one per asteroid)."""
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    diffs = np.array([stat(rng.choice(a, len(a))) - stat(rng.choice(b, len(b))) for _ in range(n_boot)])
    lo, hi = np.quantile(diffs, [(1 - level) / 2, 1 - (1 - level) / 2])
    return stat(a) - stat(b), lo, hi


def style():
    """One plotting style for every figure."""
    plt.rcParams.update({
        "figure.dpi": 100, "savefig.dpi": 150, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.3, "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.labelsize": 10, "legend.frameon": False,
    })


def finish(fig, name, title, subtitle, caption):
    """Title states the finding, subtitle the question, caption n and flag filter; saved to figures/<name>.png."""
    fig.tight_layout(rect=(0, 0.07, 1, 0.84))
    fig.text(0.01, 0.995, title, ha="left", va="top", fontsize=13, fontweight="bold")
    fig.text(0.01, 0.915, subtitle, ha="left", va="top", fontsize=10, color="0.35")
    fig.text(0.01, 0.005, caption, ha="left", va="bottom", fontsize=8, color="0.35", wrap=True)
    FIGURES.mkdir(exist_ok=True)
    path = FIGURES / f"{name}.png"
    fig.savefig(path, bbox_inches="tight")
    return path
