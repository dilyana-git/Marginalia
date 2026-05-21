from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel

from app.models.enums import JournalKind


class JournalEntry(SQLModel, table=True):
    __tablename__ = "journalentry"

    id: int | None = Field(default=None, primary_key=True)
    work_id: int | None = Field(default=None, foreign_key="work.id", index=True)
    date: date
    title: str | None = None
    body: str
    kind: JournalKind = Field(default=JournalKind.reflection, sa_column_kwargs={"index": True})
    page_or_location: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class JournalTag(SQLModel, table=True):
    __tablename__ = "journaltag"

    entry_id: int = Field(foreign_key="journalentry.id", primary_key=True, ondelete="CASCADE")
    tag_id: int = Field(foreign_key="tag.id", primary_key=True, ondelete="CASCADE")
