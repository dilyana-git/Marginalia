from datetime import datetime

from pydantic import BaseModel

from app.models.enums import FeedKind, FeedType, SeedOrigin


class FeedCreate(BaseModel):
    name: str
    type: FeedType
    kind: FeedKind
    url: str
    region_id: int | None = None
    active: bool = True
    notes: str | None = None
    seed_origin: SeedOrigin = SeedOrigin.manual


class FeedUpdate(BaseModel):
    name: str | None = None
    type: FeedType | None = None
    kind: FeedKind | None = None
    url: str | None = None
    region_id: int | None = None
    active: bool | None = None
    notes: str | None = None


class FeedRead(BaseModel):
    id: int
    name: str
    type: FeedType
    kind: FeedKind
    url: str
    region_id: int | None
    active: bool
    notes: str | None
    last_fetched_at: datetime | None
    last_status: str | None
    seed_origin: SeedOrigin
    created_at: datetime
    updated_at: datetime


class FeedCheckResult(BaseModel):
    ok: bool
    entries_count: int
    errors: list[str] = []
