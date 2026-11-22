"""Forward-only SQLite migrations: db/migrations/NNN_name.sql, applied once each, in version order."""
import pathlib

MIGRATIONS = pathlib.Path(__file__).resolve().parent / "db" / "migrations"


def _ensure(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")


def applied(conn):
    _ensure(conn)
    return [row[0] for row in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]


def apply_file(conn, path):
    """Apply one migration file atomically and record its version (the digits before the first underscore)."""
    path = pathlib.Path(path)
    version = path.name.split("_", 1)[0]
    if not version.isdigit():
        raise ValueError(f"bad migration name: {path.name}")
    _ensure(conn)
    try:
        conn.executescript(f"BEGIN;\n{path.read_text()}\nINSERT INTO schema_migrations (version) VALUES ('{version}');\nCOMMIT;")
    except Exception:
        conn.rollback()
        raise
    return version


def apply_all(conn, directory=MIGRATIONS):
    """Apply every pending migration in `directory`; return the versions applied by this call."""
    done = set(applied(conn))
    return [apply_file(conn, path) for path in sorted(pathlib.Path(directory).glob("*.sql")) if path.name.split("_", 1)[0] not in done]
