"""Connect to the local Postgres, load AGE, and set the search path.

Every Cypher call in the project goes through a connection prepared here, so the
reader sees exactly the two lines (`LOAD 'age'` + `search_path`) that make Cypher
run inside Postgres. ``age_available`` lets notebooks and tests degrade to the pure
baselines when AGE is not installed.
"""

from typing import Any

import psycopg

from src.config import Settings, load_settings

SEARCH_PATH = 'ag_catalog, "$user", public'


def prepare_connection(conn: psycopg.Connection[Any]) -> None:
    """Load the AGE extension and put ``ag_catalog`` on the search path."""
    conn.execute("LOAD 'age';")
    conn.execute(f"SET search_path = {SEARCH_PATH};")


def get_connection(settings: Settings | None = None) -> psycopg.Connection[Any]:
    """Open an autocommit connection to the local Postgres with AGE ready to use."""
    settings = settings or load_settings()
    conn = psycopg.connect(settings.db.conninfo, autocommit=True)
    prepare_connection(conn)
    return conn


def age_available(settings: Settings | None = None) -> bool:
    """True when a local Postgres is reachable *and* AGE is usable there.

    Requires the extension to be created in the target database (not merely the
    library installed), so Cypher calls will actually run.
    """
    try:
        conn = get_connection(settings)
    except Exception:
        return False
    try:
        row = conn.execute("SELECT count(*) FROM pg_extension WHERE extname = 'age'").fetchone()
        return bool(row and row[0])
    except Exception:
        return False
    finally:
        conn.close()
