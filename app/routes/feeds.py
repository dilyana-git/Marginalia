from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_api_key
from app.models import Feed
from app.models.enums import FeedKind
from app.schemas.feed import FeedCheckResult, FeedCreate, FeedRead, FeedUpdate

router = APIRouter(prefix="/feeds", tags=["feeds"], dependencies=[Depends(require_api_key)])


def _not_found(feed_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"title": "Not Found", "status": 404, "detail": f"Feed {feed_id} not found."},
    )


def _to_read(feed: Feed) -> FeedRead:
    return FeedRead.model_validate(feed, from_attributes=True)


@router.get("", response_model=list[FeedRead])
def list_feeds(
    region_id: int | None = None,
    kind: FeedKind | None = None,
    active: bool | None = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[FeedRead]:
    stmt = select(Feed)
    if region_id is not None:
        stmt = stmt.where(Feed.region_id == region_id)
    if kind is not None:
        stmt = stmt.where(Feed.kind == kind)
    if active is not None:
        stmt = stmt.where(Feed.active == active)
    stmt = stmt.offset(offset).limit(limit)
    return [_to_read(f) for f in session.exec(stmt).all()]


@router.post("", response_model=FeedRead, status_code=status.HTTP_201_CREATED)
def create_feed(body: FeedCreate, session: Session = Depends(get_session)) -> FeedRead:
    now = datetime.now(UTC)
    feed = Feed(**body.model_dump(), created_at=now, updated_at=now)
    session.add(feed)
    session.commit()
    session.refresh(feed)
    return _to_read(feed)


@router.get("/{feed_id}", response_model=FeedRead)
def get_feed(feed_id: int, session: Session = Depends(get_session)) -> FeedRead:
    feed = session.get(Feed, feed_id)
    if not feed:
        raise _not_found(feed_id)
    return _to_read(feed)


@router.put("/{feed_id}", response_model=FeedRead)
def update_feed(
    feed_id: int, body: FeedUpdate, session: Session = Depends(get_session)
) -> FeedRead:
    feed = session.get(Feed, feed_id)
    if not feed:
        raise _not_found(feed_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(feed, field, value)
    feed.updated_at = datetime.now(UTC)
    session.add(feed)
    session.commit()
    session.refresh(feed)
    return _to_read(feed)


@router.delete("/{feed_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feed(feed_id: int, session: Session = Depends(get_session)) -> None:
    feed = session.get(Feed, feed_id)
    if not feed:
        raise _not_found(feed_id)
    session.delete(feed)
    session.commit()


@router.post("/{feed_id}/check", response_model=FeedCheckResult)
def check_feed(feed_id: int, session: Session = Depends(get_session)) -> FeedCheckResult:
    import feedparser

    feed = session.get(Feed, feed_id)
    if not feed:
        raise _not_found(feed_id)

    errors: list[str] = []
    entries_count = 0
    ok = False

    try:
        parsed = feedparser.parse(feed.url)
        if parsed.bozo and parsed.bozo_exception:
            errors.append(str(parsed.bozo_exception))
        entries_count = len(parsed.entries)
        ok = entries_count > 0 or not errors
        feed.last_status = f"ok: {entries_count} entries" if ok else f"error: {errors[0]}"
    except Exception as exc:
        errors.append(str(exc))
        feed.last_status = f"error: {exc}"

    feed.last_fetched_at = datetime.now(UTC)
    feed.updated_at = datetime.now(UTC)
    session.add(feed)
    session.commit()

    return FeedCheckResult(ok=ok, entries_count=entries_count, errors=errors)
