from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Region(SQLModel, table=True):
    __tablename__ = "region"

    id: int | None = Field(default=None, primary_key=True)
    ordinal: int = Field(unique=True, index=True)
    name: str = Field(unique=True, index=True)
    qualifier: str | None = None
    why: str
    rank_note: str | None = None
    anchor: str | None = None
    color: str | None = None
    icon: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
