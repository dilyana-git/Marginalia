"""Shared fixtures: in-memory SQLite + TestClient."""

from datetime import UTC

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from app.models import (
    AppSettings,
    Feed,
    FeedKind,
    FeedType,
    ReadingList,
    Region,
    SeedOrigin,
    Work,
    WorkFormat,
    WorkTier,
)

TEST_DB_URL = "sqlite://"  # in-memory


@pytest.fixture(name="engine", scope="function")
def engine_fixture():
    # StaticPool keeps a single connection so all sessions share the same in-memory DB
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session", scope="function")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client", scope="function")
def client_fixture(engine):
    def _get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(name="region", scope="function")
def region_fixture(session: Session) -> Region:
    r = Region(ordinal=1, name="Test Region", why="because", created_at=_now(), updated_at=_now())
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


@pytest.fixture(name="work", scope="function")
def work_fixture(session: Session, region: Region) -> Work:
    from datetime import datetime

    now = datetime.now(UTC)
    w = Work(
        title="Test Book",
        authors=["Author One"],
        format=WorkFormat.book,
        tier=WorkTier.ridge,
        region_id=region.id,
        seed_origin=SeedOrigin.manual,
        date_added=now,
        created_at=now,
        updated_at=now,
    )
    session.add(w)
    session.commit()
    session.refresh(w)
    return w


@pytest.fixture(name="feed", scope="function")
def feed_fixture(session: Session, region: Region) -> Feed:
    from datetime import datetime

    now = datetime.now(UTC)
    f = Feed(
        name="Test Feed",
        type=FeedType.rss,
        kind=FeedKind.blog,
        url="https://example.com/feed",
        region_id=region.id,
        seed_origin=SeedOrigin.manual,
        active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(f)
    session.commit()
    session.refresh(f)
    return f


@pytest.fixture(name="settings_obj", scope="function")
def settings_fixture(session: Session) -> AppSettings:
    s = AppSettings(id=1, reader_name="Dilyana", reader_interests="test", timezone="Europe/Sofia")
    session.add(s)
    session.commit()
    session.refresh(s)
    return s


@pytest.fixture(name="system_list", scope="function")
def system_list_fixture(session: Session) -> ReadingList:
    from datetime import datetime

    lst = ReadingList(
        name="Currently Reading",
        is_system=True,
        created_at=datetime.now(UTC),
    )
    session.add(lst)
    session.commit()
    session.refresh(lst)
    return lst


def _now():
    from datetime import datetime

    return datetime.now(UTC)
