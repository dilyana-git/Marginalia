from datetime import datetime

from pydantic import BaseModel

from app.schemas.work import WorkRead


class ReadingListCreate(BaseModel):
    name: str
    description: str | None = None


class ReadingListUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ListItemCreate(BaseModel):
    work_id: int
    position: int | None = None
    note: str | None = None


class ListItemUpdate(BaseModel):
    position: int | None = None
    note: str | None = None


class ListItemRead(BaseModel):
    id: int
    list_id: int
    work_id: int
    position: int
    added_at: datetime
    note: str | None
    work: WorkRead | None = None


class ReadingListRead(BaseModel):
    id: int
    name: str
    description: str | None
    is_system: bool
    created_at: datetime


class ReadingListDetail(ReadingListRead):
    items: list[ListItemRead] = []
