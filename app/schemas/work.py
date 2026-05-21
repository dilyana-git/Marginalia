from datetime import date, datetime

from pydantic import BaseModel, field_validator

from app.models.enums import SeedOrigin, WorkFormat, WorkStatus, WorkTier


class WorkCreate(BaseModel):
    title: str
    subtitle: str | None = None
    authors: list[str] = []
    year: int | None = None
    format: WorkFormat = WorkFormat.other
    region_id: int | None = None
    tier: WorkTier = WorkTier.unranked
    source_name: str | None = None
    url: str | None = None
    isbn: str | None = None
    description: str | None = None
    notes: str | None = None
    status: WorkStatus = WorkStatus.want
    date_started: date | None = None
    date_finished: date | None = None
    rating: int | None = None
    is_start_here: bool = False
    seed_origin: SeedOrigin = SeedOrigin.manual

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("rating must be between 1 and 5")
        return v


class WorkUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    authors: list[str] | None = None
    year: int | None = None
    format: WorkFormat | None = None
    region_id: int | None = None
    tier: WorkTier | None = None
    source_name: str | None = None
    url: str | None = None
    isbn: str | None = None
    description: str | None = None
    notes: str | None = None
    status: WorkStatus | None = None
    date_started: date | None = None
    date_finished: date | None = None
    rating: int | None = None
    is_start_here: bool | None = None

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("rating must be between 1 and 5")
        return v


class WorkStatusPatch(BaseModel):
    status: WorkStatus


class WorkRead(BaseModel):
    id: int
    title: str
    subtitle: str | None
    authors: list[str]
    year: int | None
    format: WorkFormat
    region_id: int | None
    tier: WorkTier
    source_name: str | None
    url: str | None
    isbn: str | None
    description: str | None
    notes: str | None
    status: WorkStatus
    date_added: datetime
    date_started: date | None
    date_finished: date | None
    rating: int | None
    is_start_here: bool
    seed_origin: SeedOrigin
    created_at: datetime
    updated_at: datetime
