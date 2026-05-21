from datetime import UTC, datetime

from sqlmodel import Field, SQLModel

from app.models.enums import FeedKind, FeedType, SeedOrigin


class Feed(SQLModel, table=True):
    __tablename__ = "feed"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    type: FeedType
    kind: FeedKind
    url: str = Field(unique=True, index=True)
    region_id: int | None = Field(default=None, foreign_key="region.id", index=True)
    active: bool = Field(default=True)
    notes: str | None = None
    last_fetched_at: datetime | None = None
    last_status: str | None = None
    seed_origin: SeedOrigin = Field(default=SeedOrigin.manual)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
