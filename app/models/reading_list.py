from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class ReadingList(SQLModel, table=True):
    __tablename__ = "readinglist"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    is_system: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ListItem(SQLModel, table=True):
    __tablename__ = "listitem"
    __table_args__ = (UniqueConstraint("list_id", "work_id"),)

    id: int | None = Field(default=None, primary_key=True)
    list_id: int = Field(foreign_key="readinglist.id", ondelete="CASCADE", index=True)
    work_id: int = Field(foreign_key="work.id", ondelete="CASCADE", index=True)
    position: int = Field(default=0)
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    note: str | None = None
