import sqlite3
from datetime import date, datetime

# Path to the SQLite database file. Tests pass ':memory:' to get_connection() instead.
DB_PATH = 'chemo_dashboard.db'

# Python 3.12+ requires explicit adapters to convert date/datetime objects
# to strings when saving, and back to date/datetime objects when reading.
# detect_types=PARSE_DECLTYPES in get_connection() activates the converters below.
sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
sqlite3.register_converter('DATE', lambda b: date.fromisoformat(b.decode()))
sqlite3.register_converter('TIMESTAMP', lambda b: datetime.fromisoformat(b.decode()))


def get_connection(db_path=None):
    """Return a connection to the SQLite database.

    Pass ':memory:' for an isolated in-memory database (used in tests).
    """
    return sqlite3.connect(db_path or DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    # Returns a sqlite3.Connection — all queries and inserts go through this object.


def create_tables(conn=None, db_path=None):
    """Apply all pending schema migrations.

    Kept for backward-compatibility with v1.0 callers and tests. New code
    should call migrations.run_migrations() directly.
    """
    from migrations import run_migrations

    close_after = conn is None
    if conn is None:
        conn = get_connection()

    run_migrations(conn, db_path)

    if close_after:
        conn.close()


if __name__ == "__main__":
    create_tables(db_path=DB_PATH)
    print("Database migrated successfully.")
