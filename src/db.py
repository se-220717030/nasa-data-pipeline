
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "asteroids.db"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"


def connect(db_path=DB_PATH):
    """Connect to SQLite and enable foreign-key enforcement."""
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path=DB_PATH):
    """Create the database schema if it does not already exist."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with connect(db_path) as connection:
        connection.executescript(schema)


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized: {DB_PATH}")
