from datetime import datetime

from pydantic import BaseModel


class RegionCreate(BaseModel):
    ordinal: int
    name: str
    qualifier: str | None = None
    why: str
    rank_note: str | None = None
    anchor: str | None = None
    color: str | None = None
    icon: str | None = None


class RegionUpdate(BaseModel):
    ordinal: int | None = None
    name: str | None = None
    qualifier: str | None = None
    why: str | None = None
    rank_note: str | None = None
    anchor: str | None = None
    color: str | None = None
    icon: str | None = None


class RegionRead(BaseModel):
    id: int
    ordinal: int
    name: str
    qualifier: str | None
    why: str
    rank_note: str | None
    anchor: str | None
    color: str | None
    icon: str | None
    created_at: datetime
    updated_at: datetime


class RegionDetail(RegionRead):
    works_count: int = 0
    journal_count: int = 0
    feeds_count: int = 0
