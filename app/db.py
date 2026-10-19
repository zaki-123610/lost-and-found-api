from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

import psycopg
from fastapi import Depends
from psycopg.rows import dict_row

from app.core.config import DATABASE_URL

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


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


# Endpoints declare `conn: DbConn` to receive a per-request connection.
DbConn = Annotated[psycopg.Connection, Depends(get_db)]


def init_db() -> None:
    """Create the tables if they don't exist yet. Safe to run on every startup."""
    with get_connection() as conn:
        conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
