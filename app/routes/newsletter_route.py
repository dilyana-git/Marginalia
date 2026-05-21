from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_api_key
from app.models import Feed, NewsletterItem, NewsletterRun, Work
from app.models.enums import NewsletterItemStatus, SeedOrigin, WorkFormat, WorkStatus, WorkTier
from app.schemas.newsletter import (
    NewsletterItemPatch,
    NewsletterItemRead,
    NewsletterRunRead,
    NewsletterRunRequest,
)

router = APIRouter(
    prefix="/newsletter", tags=["newsletter"], dependencies=[Depends(require_api_key)]
)


@router.post("/run", response_model=NewsletterRunRead)
def trigger_run(
    body: NewsletterRunRequest, session: Session = Depends(get_session)
) -> NewsletterRunRead:
    from app.newsletter.runner import run as newsletter_run

    result = newsletter_run(session=session, send=body.send)
    return NewsletterRunRead.model_validate(result, from_attributes=True)


@router.get("/items", response_model=list[NewsletterItemRead])
def list_items(
    status_filter: NewsletterItemStatus | None = Query(None, alias="status"),
    region_id: int | None = None,
    date_from: datetime | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[NewsletterItemRead]:
    stmt = select(NewsletterItem)
    if status_filter is not None:
        stmt = stmt.where(NewsletterItem.status == status_filter)
    if region_id is not None:
        stmt = stmt.join(Feed, NewsletterItem.feed_id == Feed.id).where(
            Feed.region_id == region_id
        )
    if date_from is not None:
        stmt = stmt.where(NewsletterItem.created_at >= date_from)
    stmt = stmt.order_by(NewsletterItem.created_at.desc()).offset(offset).limit(limit)  # type: ignore[attr-defined]
    return [NewsletterItemRead.model_validate(ni, from_attributes=True) for ni in session.exec(stmt).all()]


@router.patch("/items/{item_id}", response_model=NewsletterItemRead)
def patch_item(
    item_id: int, body: NewsletterItemPatch, session: Session = Depends(get_session)
) -> NewsletterItemRead:
    item = session.get(NewsletterItem, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"title": "Not Found", "status": 404, "detail": f"NewsletterItem {item_id} not found."},
        )

    if body.status is not None:
        item.status = body.status

    if body.save_as_work and item.status == NewsletterItemStatus.saved_to_works:
        tier_val = body.save_as_work.get("tier", WorkTier.unranked)
        work = Work(
            title=item.title,
            authors=[],
            url=item.link,
            format=WorkFormat.article,
            status=WorkStatus.saved,
            region_id=body.save_as_work.get("region_id"),
            tier=WorkTier(tier_val) if isinstance(tier_val, str) else tier_val,
            seed_origin=SeedOrigin.manual,
            date_added=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(work)
        session.flush()
        item.saved_work_id = work.id

    session.add(item)
    session.commit()
    session.refresh(item)
    return NewsletterItemRead.model_validate(item, from_attributes=True)


@router.get("/runs", response_model=list[NewsletterRunRead])
def list_runs(
    limit: int = Query(20, le=100),
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[NewsletterRunRead]:
    runs = session.exec(
        select(NewsletterRun).order_by(NewsletterRun.ran_at.desc()).offset(offset).limit(limit)  # type: ignore[attr-defined]
    ).all()
    return [NewsletterRunRead.model_validate(r, from_attributes=True) for r in runs]
