from fastapi import APIRouter, status

from app.db import DbConn
from app.dependencies import CurrentUserId
from app.schemas.items import ItemCreate, ItemOut

router = APIRouter(prefix="/items", tags=["items"])


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
