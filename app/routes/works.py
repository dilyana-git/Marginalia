from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_api_key
from app.models import JournalEntry, Work, WorkTag
from app.models.enums import WorkFormat, WorkStatus, WorkTier
from app.schemas.journal import JournalEntryRead
from app.schemas.work import WorkCreate, WorkRead, WorkStatusPatch, WorkUpdate

router = APIRouter(prefix="/works", tags=["works"], dependencies=[Depends(require_api_key)])


def _not_found(work_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"title": "Not Found", "status": 404, "detail": f"Work {work_id} not found."},
    )


def _to_read(work: Work) -> WorkRead:
    return WorkRead.model_validate(work, from_attributes=True)


@router.get("", response_model=list[WorkRead])
def list_works(
    region_id: int | None = None,
    status_filter: WorkStatus | None = Query(None, alias="status"),
    tier: WorkTier | None = None,
    format: WorkFormat | None = None,
    tag: int | None = None,
    q: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[WorkRead]:
    stmt = select(Work)
    if region_id is not None:
        stmt = stmt.where(Work.region_id == region_id)
    if status_filter is not None:
        stmt = stmt.where(Work.status == status_filter)
    if tier is not None:
        stmt = stmt.where(Work.tier == tier)
    if format is not None:
        stmt = stmt.where(Work.format == format)
    if tag is not None:
        stmt = stmt.join(WorkTag, Work.id == WorkTag.work_id).where(WorkTag.tag_id == tag)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            Work.title.ilike(like)  # type: ignore[attr-defined]
            | Work.description.ilike(like)  # type: ignore[attr-defined]
        )
    stmt = stmt.offset(offset).limit(limit)
    return [_to_read(w) for w in session.exec(stmt).all()]


@router.post("", response_model=WorkRead, status_code=status.HTTP_201_CREATED)
def create_work(body: WorkCreate, session: Session = Depends(get_session)) -> WorkRead:
    now = datetime.now(UTC)
    work = Work(
        **body.model_dump(exclude={"rating"}),
        rating=body.rating,
        date_added=now,
        created_at=now,
        updated_at=now,
    )
    session.add(work)
    session.commit()
    session.refresh(work)
    return _to_read(work)


@router.get("/{work_id}", response_model=WorkRead)
def get_work(work_id: int, session: Session = Depends(get_session)) -> WorkRead:
    work = session.get(Work, work_id)
    if not work:
        raise _not_found(work_id)
    return _to_read(work)


@router.put("/{work_id}", response_model=WorkRead)
def update_work(
    work_id: int, body: WorkUpdate, session: Session = Depends(get_session)
) -> WorkRead:
    work = session.get(Work, work_id)
    if not work:
        raise _not_found(work_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(work, field, value)
    work.updated_at = datetime.now(UTC)
    session.add(work)
    session.commit()
    session.refresh(work)
    return _to_read(work)


@router.delete("/{work_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work(work_id: int, session: Session = Depends(get_session)) -> None:
    work = session.get(Work, work_id)
    if not work:
        raise _not_found(work_id)
    session.delete(work)
    session.commit()


@router.patch("/{work_id}/status", response_model=WorkRead)
def patch_work_status(
    work_id: int, body: WorkStatusPatch, session: Session = Depends(get_session)
) -> WorkRead:
    work = session.get(Work, work_id)
    if not work:
        raise _not_found(work_id)
    work.status = body.status
    work.updated_at = datetime.now(UTC)
    session.add(work)
    session.commit()
    session.refresh(work)
    return _to_read(work)


@router.get("/{work_id}/journal", response_model=list[JournalEntryRead])
def get_work_journal(
    work_id: int, session: Session = Depends(get_session)
) -> list[JournalEntryRead]:
    work = session.get(Work, work_id)
    if not work:
        raise _not_found(work_id)
    entries = session.exec(
        select(JournalEntry)
        .where(JournalEntry.work_id == work_id)
        .order_by(JournalEntry.date.desc())  # type: ignore[attr-defined]
    ).all()
    return [JournalEntryRead.model_validate(e, from_attributes=True) for e in entries]
