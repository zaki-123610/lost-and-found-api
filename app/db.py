from collections.abc import Iterator

import psycopg
from psycopg.rows import dict_row

from app.core.config import DATABASE_URL


def get_connection() -> psycopg.Connection:
    """Open a new PostgreSQL connection.

    Rows come back as dicts and each statement is committed immediately
    (autocommit). Wrap multi-statement work in `with conn.transaction():`.
    """
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=True)


def get_db() -> Iterator[psycopg.Connection]:
    """FastAPI dependency: one connection per request, always closed afterwards."""
    with get_connection() as conn:
        yield conn
