from datetime import UTC, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.enums import NewsletterItemStatus


class NewsletterRun(SQLModel, table=True):
    __tablename__ = "newsletterrun"

    id: int | None = Field(default=None, primary_key=True)
    ran_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    items_count: int = Field(default=0)
    sent: bool = Field(default=False)
    recipient: str | None = None
    intro_text: str | None = None
    error_log: str | None = None


class NewsletterItem(SQLModel, table=True):
    __tablename__ = "newsletteritem"
    __table_args__ = (UniqueConstraint("feed_id", "external_id"),)

    id: int | None = Field(default=None, primary_key=True)
    feed_id: int = Field(foreign_key="feed.id", index=True)
    external_id: str = Field(index=True)
    title: str
    link: str | None = None
    published_at: datetime | None = None
    snippet: str
    claude_blurb: str | None = None
    is_highlight: bool = Field(default=False)
    status: NewsletterItemStatus = Field(
        default=NewsletterItemStatus.new, sa_column_kwargs={"index": True}
    )
    saved_work_id: int | None = Field(default=None, foreign_key="work.id")
    sent_in_run_id: int | None = Field(default=None, foreign_key="newsletterrun.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
