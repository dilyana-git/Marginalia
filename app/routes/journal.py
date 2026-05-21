from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_api_key
from app.models import JournalEntry, JournalTag
from app.models.enums import JournalKind
from app.schemas.journal import JournalEntryCreate, JournalEntryRead, JournalEntryUpdate

router = APIRouter(prefix="/journal", tags=["journal"], dependencies=[Depends(require_api_key)])


def _not_found(entry_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"title": "Not Found", "status": 404, "detail": f"Journal entry {entry_id} not found."},
    )


def _to_read(entry: JournalEntry, session: Session) -> JournalEntryRead:
    tag_ids = [jt.tag_id for jt in session.exec(
        select(JournalTag).where(JournalTag.entry_id == entry.id)
    ).all()]
    return JournalEntryRead(
        **JournalEntryRead.model_validate(entry, from_attributes=True).model_dump(exclude={"tag_ids"}),
        tag_ids=tag_ids,
    )


def _sync_tags(session: Session, entry_id: int, tag_ids: list[int]) -> None:
    existing = session.exec(select(JournalTag).where(JournalTag.entry_id == entry_id)).all()
    for jt in existing:
        session.delete(jt)
    session.flush()
    for tid in tag_ids:
        session.add(JournalTag(entry_id=entry_id, tag_id=tid))
    session.flush()


@router.get("", response_model=list[JournalEntryRead])
def list_journal(
    work_id: int | None = None,
    tag: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    kind: JournalKind | None = None,
    q: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[JournalEntryRead]:
    stmt = select(JournalEntry)
    if work_id is not None:
        stmt = stmt.where(JournalEntry.work_id == work_id)
    if kind is not None:
        stmt = stmt.where(JournalEntry.kind == kind)
    if date_from is not None:
        stmt = stmt.where(JournalEntry.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(JournalEntry.date <= date_to)
    if tag is not None:
        stmt = stmt.join(JournalTag, JournalEntry.id == JournalTag.entry_id).where(
            JournalTag.tag_id == tag
        )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            JournalEntry.body.ilike(like)  # type: ignore[attr-defined]
            | JournalEntry.title.ilike(like)  # type: ignore[attr-defined]
        )
    stmt = stmt.order_by(JournalEntry.date.desc()).offset(offset).limit(limit)  # type: ignore[attr-defined]
    return [_to_read(e, session) for e in session.exec(stmt).all()]


@router.post("", response_model=JournalEntryRead, status_code=status.HTTP_201_CREATED)
def create_entry(body: JournalEntryCreate, session: Session = Depends(get_session)) -> JournalEntryRead:
    now = datetime.now(timezone.utc)
    entry = JournalEntry(
        **body.model_dump(exclude={"tag_ids"}),
        created_at=now,
        updated_at=now,
    )
    session.add(entry)
    session.flush()
    _sync_tags(session, entry.id, body.tag_ids)  # type: ignore[arg-type]
    session.commit()
    session.refresh(entry)
    return _to_read(entry, session)


@router.get("/{entry_id}", response_model=JournalEntryRead)
def get_entry(entry_id: int, session: Session = Depends(get_session)) -> JournalEntryRead:
    entry = session.get(JournalEntry, entry_id)
    if not entry:
        raise _not_found(entry_id)
    return _to_read(entry, session)


@router.put("/{entry_id}", response_model=JournalEntryRead)
def update_entry(
    entry_id: int, body: JournalEntryUpdate, session: Session = Depends(get_session)
) -> JournalEntryRead:
    entry = session.get(JournalEntry, entry_id)
    if not entry:
        raise _not_found(entry_id)
    for field, value in body.model_dump(exclude_unset=True, exclude={"tag_ids"}).items():
        setattr(entry, field, value)
    entry.updated_at = datetime.now(timezone.utc)
    session.add(entry)
    session.flush()
    if body.tag_ids is not None:
        _sync_tags(session, entry_id, body.tag_ids)
    session.commit()
    session.refresh(entry)
    return _to_read(entry, session)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, session: Session = Depends(get_session)) -> None:
    entry = session.get(JournalEntry, entry_id)
    if not entry:
        raise _not_found(entry_id)
    session.delete(entry)
    session.commit()
