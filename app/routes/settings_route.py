
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_api_key
from app.models import AppSettings
from app.schemas.settings import SettingsRead, SettingsUpdate

router = APIRouter(
    prefix="/settings", tags=["settings"], dependencies=[Depends(require_api_key)]
)


def _get_or_create(session: Session) -> AppSettings:
    s = session.exec(select(AppSettings).where(AppSettings.id == 1)).first()
    if s is None:
        s = AppSettings(id=1)
        session.add(s)
        session.commit()
        session.refresh(s)
    return s


@router.get("", response_model=SettingsRead)
def get_settings(session: Session = Depends(get_session)) -> AppSettings:
    return _get_or_create(session)


@router.put("", response_model=SettingsRead)
def update_settings(
    body: SettingsUpdate, session: Session = Depends(get_session)
) -> AppSettings:
    s = _get_or_create(session)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(s, field, value)
    session.add(s)
    session.commit()
    session.refresh(s)
    return s
