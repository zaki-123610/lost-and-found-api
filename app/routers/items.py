from typing import Annotated

import psycopg
from fastapi import APIRouter, HTTPException, Query, status
from psycopg import sql

from app.db import DbConn
from app.dependencies import CurrentUserId
from app.schemas.items import ItemCreate, ItemFilters, ItemList, ItemOut

router = APIRouter(prefix="/items", tags=["items"])


def _contains(text: str) -> str:
    """ILIKE pattern matching `text` anywhere, with % and _ taken literally."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _where_clause(filters: ItemFilters) -> tuple[sql.Composable, list[object]]:
    """Build the WHERE clause for the given filters. Values are always passed as parameters."""
    conditions: list[sql.Composable] = []
    params: list[object] = []
    if filters.type:
        conditions.append(sql.SQL("type = %s"))
        params.append(filters.type)
    if filters.category:
        conditions.append(sql.SQL("category = %s"))
        params.append(filters.category)
    if filters.status:
        conditions.append(sql.SQL("status = %s"))
        params.append(filters.status)
    if filters.location:
        conditions.append(sql.SQL("location ILIKE %s"))
        params.append(_contains(filters.location))
    if filters.q:
        conditions.append(sql.SQL("(title ILIKE %s OR description ILIKE %s)"))
        params += [_contains(filters.q)] * 2
    if filters.date_from:
        conditions.append(sql.SQL("event_date >= %s"))
        params.append(filters.date_from)
    if filters.date_to:
        conditions.append(sql.SQL("event_date <= %s"))
        params.append(filters.date_to)
    if not conditions:
        return sql.SQL(""), params
    return sql.SQL("WHERE ") + sql.SQL(" AND ").join(conditions), params


def _get_item_or_404(conn: psycopg.Connection, item_id: int) -> dict:
    item = conn.execute("SELECT * FROM items WHERE id = %s", (item_id,)).fetchone()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.post("", status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, user_id: CurrentUserId, conn: DbConn) -> ItemOut:
    """Report a lost or found item. It belongs to the caller and starts as `open`."""
    row = conn.execute(
        """
        INSERT INTO items (user_id, type, title, description, category, location, event_date)
        VALUES (%(user_id)s, %(type)s, %(title)s, %(description)s,
                %(category)s, %(location)s, %(event_date)s)
        RETURNING *
        """,
        {"user_id": user_id, **item.model_dump()},
    ).fetchone()
    return ItemOut.model_validate(row)


@router.get("")
def list_items(filters: Annotated[ItemFilters, Query()], conn: DbConn) -> ItemList:
    """Search reported items, newest first. Public: no token needed."""
    where, params = _where_clause(filters)
    total = conn.execute(
        sql.SQL("SELECT count(*) AS total FROM items {}").format(where), params
    ).fetchone()["total"]
    rows = conn.execute(
        sql.SQL(
            "SELECT * FROM items {} ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
        ).format(where),
        [*params, filters.page_size, (filters.page - 1) * filters.page_size],
    ).fetchall()
    return ItemList(
        items=[ItemOut.model_validate(row) for row in rows],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
    )


@router.get("/{item_id}")
def get_item(item_id: int, conn: DbConn) -> ItemOut:
    """Show one item. Public: no token needed."""
    return ItemOut.model_validate(_get_item_or_404(conn, item_id))
