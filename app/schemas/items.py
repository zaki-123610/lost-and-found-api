from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

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


class ItemUpdate(BaseModel):
    """Body of PATCH /items/{id}. Only the fields that are sent are changed."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"title": "Brown leather wallet", "location": "Hydra"}]},
    )

    type: ItemType | None = None
    title: Title | None = None
    description: Description | None = None
    category: ItemCategory | None = None
    location: Location | None = None
    event_date: EventDate | None = None

    @field_validator("type", "title", "category", "location", "event_date")
    @classmethod
    def not_null(cls, value: object) -> object:
        # Required columns can be left out of the body, but not set to null.
        if value is None:
            raise ValueError("Cannot be null")
        return value


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


SearchText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]


class ItemFilters(BaseModel):
    """Query parameters of GET /items. All filters are optional and combined with AND."""

    type: ItemType | None = None
    category: ItemCategory | None = None
    status: ItemStatus | None = None
    location: SearchText | None = Field(None, description="Part of the location, case-insensitive")
    q: SearchText | None = Field(None, description="Keyword searched in title and description")
    date_from: date | None = Field(None, description="Lost/found on or after this date")
    date_to: date | None = Field(None, description="Lost/found on or before this date")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @model_validator(mode="after")
    def check_date_range(self) -> Self:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to")
        return self


class ItemList(BaseModel):
    items: list[ItemOut]
    total: int
    page: int
    page_size: int
