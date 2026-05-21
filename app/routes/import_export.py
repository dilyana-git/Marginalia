import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_api_key
from app.models import (
    AppSettings,
    Feed,
    JournalEntry,
    JournalTag,
    ListItem,
    NewsletterItem,
    NewsletterRun,
    ReadingList,
    Region,
    Tag,
    Work,
    WorkTag,
)
from app.services.seeding import SEED_PATH, run_seed

router = APIRouter(
    prefix="/import-export", tags=["import/export"], dependencies=[Depends(require_api_key)]
)


class ImportRequest(BaseModel):
    mode: str = "merge"  # "merge" | "replace"


@router.post("/import", status_code=status.HTTP_200_OK)
def import_seed(body: ImportRequest, session: Session = Depends(get_session)) -> dict:
    if body.mode not in ("merge", "replace"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "title": "Validation Error",
                "status": 422,
                "detail": "mode must be 'merge' or 'replace'",
            },
        )
    if body.mode == "replace":
        # Truncate all data tables except migrations
        for table in [
            WorkTag, JournalTag, ListItem, NewsletterItem, JournalEntry,
            Work, Feed, ReadingList, Tag, Region, NewsletterRun, AppSettings
        ]:
            for row in session.exec(select(table)).all():
                session.delete(row)
        session.flush()

    counts = run_seed(session, SEED_PATH)
    return {"mode": body.mode, "imported": counts}


@router.get("/export")
def export_data(session: Session = Depends(get_session)) -> JSONResponse:
    def _ser(obj: object) -> object:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    def _rows(model_cls, stmt=None) -> list[dict]:
        rows = session.exec(stmt or select(model_cls)).all()
        return [r.model_dump() for r in rows]

    payload = {
        "exported_at": datetime.now(UTC).isoformat(),
        "regions": _rows(Region),
        "tags": _rows(Tag),
        "works": _rows(Work),
        "work_tags": _rows(WorkTag),
        "reading_lists": _rows(ReadingList),
        "list_items": _rows(ListItem),
        "journal_entries": _rows(JournalEntry),
        "journal_tags": _rows(JournalTag),
        "feeds": _rows(Feed),
        "newsletter_runs": _rows(NewsletterRun),
        "newsletter_items": _rows(NewsletterItem),
        "settings": _rows(AppSettings),
    }

    return JSONResponse(content=json.loads(json.dumps(payload, default=_ser)))
