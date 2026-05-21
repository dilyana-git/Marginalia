from datetime import date, datetime, timezone

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel

from app.models.enums import SeedOrigin, WorkFormat, WorkStatus, WorkTier


class Work(SQLModel, table=True):
    __tablename__ = "work"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    subtitle: str | None = None
    authors: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    year: int | None = None
    format: WorkFormat = Field(default=WorkFormat.other, sa_column_kwargs={"index": True})
    region_id: int | None = Field(default=None, foreign_key="region.id", index=True)
    tier: WorkTier = Field(default=WorkTier.unranked, sa_column_kwargs={"index": True})
    source_name: str | None = None
    url: str | None = None
    isbn: str | None = None
    description: str | None = None
    notes: str | None = None
    status: WorkStatus = Field(default=WorkStatus.want, sa_column_kwargs={"index": True})
    date_added: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    date_started: date | None = None
    date_finished: date | None = None
    rating: int | None = None
    is_start_here: bool = Field(default=False)
    seed_origin: SeedOrigin = Field(default=SeedOrigin.manual)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkTag(SQLModel, table=True):
    __tablename__ = "worktag"

    work_id: int = Field(foreign_key="work.id", primary_key=True, ondelete="CASCADE")
    tag_id: int = Field(foreign_key="tag.id", primary_key=True, ondelete="CASCADE")
