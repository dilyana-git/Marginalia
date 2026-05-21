from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, func, select

from app.db import get_session
from app.deps import require_api_key
from app.models import Feed, JournalEntry, Region, Work
from app.schemas.region import RegionCreate, RegionDetail, RegionRead, RegionUpdate

router = APIRouter(prefix="/regions", tags=["regions"], dependencies=[Depends(require_api_key)])


def _not_found(region_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"title": "Not Found", "status": 404, "detail": f"Region {region_id} not found."},
    )


@router.get("", response_model=list[RegionRead])
def list_regions(session: Session = Depends(get_session)) -> list[Region]:
    return list(session.exec(select(Region).order_by(Region.ordinal)).all())


@router.post("", response_model=RegionRead, status_code=status.HTTP_201_CREATED)
def create_region(body: RegionCreate, session: Session = Depends(get_session)) -> Region:
    region = Region(**body.model_dump(), created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
    session.add(region)
    session.commit()
    session.refresh(region)
    return region


@router.get("/{region_id}", response_model=RegionDetail)
def get_region(region_id: int, session: Session = Depends(get_session)) -> RegionDetail:
    region = session.get(Region, region_id)
    if not region:
        raise _not_found(region_id)

    works_count = session.exec(
        select(func.count()).where(Work.region_id == region_id)
    ).one()
    journal_count = session.exec(
        select(func.count(JournalEntry.id))
        .join(Work, JournalEntry.work_id == Work.id, isouter=True)
        .where(Work.region_id == region_id)
    ).one()
    feeds_count = session.exec(
        select(func.count()).where(Feed.region_id == region_id)
    ).one()

    return RegionDetail(
        **RegionRead.model_validate(region, from_attributes=True).model_dump(),
        works_count=works_count,
        journal_count=journal_count,
        feeds_count=feeds_count,
    )


@router.put("/{region_id}", response_model=RegionRead)
def update_region(
    region_id: int, body: RegionUpdate, session: Session = Depends(get_session)
) -> Region:
    region = session.get(Region, region_id)
    if not region:
        raise _not_found(region_id)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(region, field, value)
    region.updated_at = datetime.now(UTC)
    session.add(region)
    session.commit()
    session.refresh(region)
    return region


@router.delete("/{region_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_region(region_id: int, session: Session = Depends(get_session)) -> None:
    region = session.get(Region, region_id)
    if not region:
        raise _not_found(region_id)
    # Cascade region_id to null on Works and Feeds (SQLite doesn't enforce by default,
    # but we do it explicitly for correctness)
    for work in session.exec(select(Work).where(Work.region_id == region_id)).all():
        work.region_id = None
        session.add(work)
    for feed in session.exec(select(Feed).where(Feed.region_id == region_id)).all():
        feed.region_id = None
        session.add(feed)
    session.delete(region)
    session.commit()
