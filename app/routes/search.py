from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_api_key
from app.models import JournalEntry, NewsletterItem, Work
from app.schemas.journal import JournalEntryRead
from app.schemas.newsletter import NewsletterItemRead
from app.schemas.search import SearchResults
from app.schemas.work import WorkRead

router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=SearchResults)
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, le=100),
    session: Session = Depends(get_session),
) -> SearchResults:
    like = f"%{q}%"

    works = [
        WorkRead.model_validate(w, from_attributes=True)
        for w in session.exec(
            select(Work).where(
                Work.title.ilike(like)  # type: ignore[attr-defined]
                | Work.description.ilike(like)  # type: ignore[attr-defined]
                | Work.notes.ilike(like)  # type: ignore[attr-defined]
            ).limit(limit)
        ).all()
    ]

    journal_entries = [
        JournalEntryRead.model_validate(e, from_attributes=True)
        for e in session.exec(
            select(JournalEntry).where(
                JournalEntry.body.ilike(like)  # type: ignore[attr-defined]
                | JournalEntry.title.ilike(like)  # type: ignore[attr-defined]
            ).limit(limit)
        ).all()
    ]

    newsletter_items = [
        NewsletterItemRead.model_validate(ni, from_attributes=True)
        for ni in session.exec(
            select(NewsletterItem).where(
                NewsletterItem.title.ilike(like)  # type: ignore[attr-defined]
                | NewsletterItem.snippet.ilike(like)  # type: ignore[attr-defined]
                | NewsletterItem.claude_blurb.ilike(like)  # type: ignore[attr-defined]
            ).limit(limit)
        ).all()
    ]

    return SearchResults(
        query=q,
        works=works,
        journal_entries=journal_entries,
        newsletter_items=newsletter_items,
    )
