from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

import psycopg
from fastapi import Depends
from psycopg.rows import dict_row

from app.core.config import DATABASE_URL

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=True)


def get_db() -> Iterator[psycopg.Connection]:
    with get_connection() as conn:
        yield conn


DbConn = Annotated[psycopg.Connection, Depends(get_db)]


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
