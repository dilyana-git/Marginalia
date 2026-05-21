from pydantic import BaseModel

from app.schemas.journal import JournalEntryRead
from app.schemas.newsletter import NewsletterItemRead
from app.schemas.work import WorkRead


class SearchResults(BaseModel):
    query: str
    works: list[WorkRead] = []
    journal_entries: list[JournalEntryRead] = []
    newsletter_items: list[NewsletterItemRead] = []
