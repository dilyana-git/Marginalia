from datetime import date as DateType
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import JournalKind


class JournalEntryCreate(BaseModel):
    work_id: int | None = None
    date: DateType
    title: str | None = None
    body: str
    kind: JournalKind = JournalKind.reflection
    page_or_location: str | None = None
    tag_ids: list[int] = []


class JournalEntryUpdate(BaseModel):
    work_id: int | None = None
    date: DateType | None = None
    title: str | None = None
    body: str | None = None
    kind: JournalKind | None = None
    page_or_location: str | None = None
    tag_ids: list[int] | None = None


class JournalEntryRead(BaseModel):
    id: int
    work_id: int | None
    date: DateType
    title: str | None
    body: str
    kind: JournalKind
    page_or_location: str | None
    created_at: datetime
    updated_at: datetime
    tag_ids: list[int] = []
