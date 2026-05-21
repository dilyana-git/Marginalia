from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_api_key
from app.models import ListItem, ReadingList, Work
from app.schemas.reading_list import (
    ListItemCreate,
    ListItemRead,
    ListItemUpdate,
    ReadingListCreate,
    ReadingListDetail,
    ReadingListRead,
    ReadingListUpdate,
)
from app.schemas.work import WorkRead

router = APIRouter(prefix="/lists", tags=["lists"], dependencies=[Depends(require_api_key)])


def _not_found(list_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"title": "Not Found", "status": 404, "detail": f"List {list_id} not found."},
    )


def _item_not_found(list_id: int, work_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"title": "Not Found", "status": 404, "detail": f"Item work={work_id} not in list {list_id}."},
    )


def _build_item_read(item: ListItem, session: Session) -> ListItemRead:
    work = session.get(Work, item.work_id)
    return ListItemRead(
        id=item.id,  # type: ignore[arg-type]
        list_id=item.list_id,
        work_id=item.work_id,
        position=item.position,
        added_at=item.added_at,
        note=item.note,
        work=WorkRead.model_validate(work, from_attributes=True) if work else None,
    )


@router.get("", response_model=list[ReadingListRead])
def list_lists(session: Session = Depends(get_session)) -> list[ReadingList]:
    return list(session.exec(select(ReadingList).order_by(ReadingList.name)).all())


@router.post("", response_model=ReadingListRead, status_code=status.HTTP_201_CREATED)
def create_list(body: ReadingListCreate, session: Session = Depends(get_session)) -> ReadingList:
    lst = ReadingList(**body.model_dump(), is_system=False, created_at=datetime.now(timezone.utc))
    session.add(lst)
    session.commit()
    session.refresh(lst)
    return lst


@router.get("/{list_id}", response_model=ReadingListDetail)
def get_list(list_id: int, session: Session = Depends(get_session)) -> ReadingListDetail:
    lst = session.get(ReadingList, list_id)
    if not lst:
        raise _not_found(list_id)
    items_orm = session.exec(
        select(ListItem).where(ListItem.list_id == list_id).order_by(ListItem.position)
    ).all()
    items = [_build_item_read(i, session) for i in items_orm]
    return ReadingListDetail(
        **ReadingListRead.model_validate(lst, from_attributes=True).model_dump(),
        items=items,
    )


@router.put("/{list_id}", response_model=ReadingListRead)
def update_list(
    list_id: int, body: ReadingListUpdate, session: Session = Depends(get_session)
) -> ReadingList:
    lst = session.get(ReadingList, list_id)
    if not lst:
        raise _not_found(list_id)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(lst, field, value)
    session.add(lst)
    session.commit()
    session.refresh(lst)
    return lst


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(list_id: int, session: Session = Depends(get_session)) -> None:
    lst = session.get(ReadingList, list_id)
    if not lst:
        raise _not_found(list_id)
    if lst.is_system:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"title": "Conflict", "status": 409, "detail": "System lists cannot be deleted."},
        )
    session.delete(lst)
    session.commit()


@router.post("/{list_id}/items", response_model=ListItemRead, status_code=status.HTTP_201_CREATED)
def add_item(
    list_id: int, body: ListItemCreate, session: Session = Depends(get_session)
) -> ListItemRead:
    lst = session.get(ReadingList, list_id)
    if not lst:
        raise _not_found(list_id)
    if not session.get(Work, body.work_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"title": "Not Found", "status": 404, "detail": f"Work {body.work_id} not found."},
        )
    # Auto-assign position if not provided
    existing = session.exec(
        select(ListItem).where(ListItem.list_id == list_id).order_by(ListItem.position.desc())  # type: ignore[attr-defined]
    ).first()
    pos = body.position if body.position is not None else ((existing.position + 1) if existing else 0)

    item = ListItem(
        list_id=list_id,
        work_id=body.work_id,
        position=pos,
        note=body.note,
        added_at=datetime.now(timezone.utc),
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return _build_item_read(item, session)


@router.put("/{list_id}/items/{work_id}", response_model=ListItemRead)
def update_item(
    list_id: int, work_id: int, body: ListItemUpdate, session: Session = Depends(get_session)
) -> ListItemRead:
    item = session.exec(
        select(ListItem).where(ListItem.list_id == list_id, ListItem.work_id == work_id)
    ).first()
    if not item:
        raise _item_not_found(list_id, work_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return _build_item_read(item, session)


@router.delete("/{list_id}/items/{work_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(list_id: int, work_id: int, session: Session = Depends(get_session)) -> None:
    item = session.exec(
        select(ListItem).where(ListItem.list_id == list_id, ListItem.work_id == work_id)
    ).first()
    if not item:
        raise _item_not_found(list_id, work_id)
    session.delete(item)
    session.commit()
