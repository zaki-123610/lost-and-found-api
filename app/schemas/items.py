from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints

ItemType = Literal["lost", "found"]
ItemStatus = Literal["open", "recovered"]
# A fixed list keeps category filters reliable ("phone" vs "Phones" would never match).
ItemCategory = Literal[
    "electronics", "documents", "keys", "wallets", "bags", "clothing", "accessories", "other"
]


def _not_in_future(value: date) -> date:
    # One day of margin: users east of UTC (Algeria is UTC+1) can be a day ahead of the server.
    if value > datetime.now(UTC).date() + timedelta(days=1):
        raise ValueError("Date cannot be in the future")
    return value


Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
Location = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
EventDate = Annotated[date, AfterValidator(_not_in_future)]


class ItemCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "type": "lost",
                    "title": "Black leather wallet",
                    "description": "Contains my student card and some cash.",
                    "category": "wallets",
                    "location": "USTHB, Bab Ezzouar",
                    "event_date": "2026-10-18",
                }
            ]
        },
    )

    type: ItemType
    title: Title
    description: Description | None = None
    category: ItemCategory
    location: Location
    event_date: EventDate


class ItemOut(BaseModel):
    id: int
    user_id: int
    type: ItemType
    title: str
    description: str | None
    category: ItemCategory
    location: str
    event_date: date
    status: ItemStatus
    created_at: datetime
    updated_at: datetime
