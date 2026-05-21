from datetime import datetime

from pydantic import BaseModel

from app.models.enums import NewsletterItemStatus


class NewsletterRunRequest(BaseModel):
    send: bool = True


class NewsletterItemPatch(BaseModel):
    status: NewsletterItemStatus | None = None
    save_as_work: dict | None = None  # {region_id?: int, tier?: str}


class NewsletterItemRead(BaseModel):
    id: int
    feed_id: int
    external_id: str
    title: str
    link: str | None
    published_at: datetime | None
    snippet: str
    claude_blurb: str | None
    is_highlight: bool
    status: NewsletterItemStatus
    saved_work_id: int | None
    sent_in_run_id: int | None
    created_at: datetime


class NewsletterRunRead(BaseModel):
    id: int
    ran_at: datetime
    items_count: int
    sent: bool
    recipient: str | None
    intro_text: str | None
    error_log: str | None
