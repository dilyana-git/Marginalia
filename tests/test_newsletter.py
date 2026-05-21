"""Newsletter pipeline tests with mocked feeds and Anthropic client."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import AppSettings, Feed, FeedKind, FeedType, NewsletterItem, SeedOrigin
from app.models.enums import NewsletterItemStatus
from app.newsletter.fetcher import fetch_all
from app.newsletter.renderer import render_html, render_plaintext
from app.newsletter.runner import run as newsletter_run


def _seed_settings(session: Session) -> AppSettings:
    s = AppSettings(
        id=1, reader_name="Dilyana", reader_interests="test interests", timezone="Europe/Sofia"
    )
    session.add(s)
    session.commit()
    session.refresh(s)
    return s


def _seed_feed(session: Session) -> Feed:
    now = datetime.now(UTC)
    f = Feed(
        name="Test Blog",
        type=FeedType.rss,
        kind=FeedKind.blog,
        url="https://example.com/feed",
        active=True,
        seed_origin=SeedOrigin.manual,
        created_at=now,
        updated_at=now,
    )
    session.add(f)
    session.commit()
    session.refresh(f)
    return f


_FAKE_FEED_ENTRY = {
    "id": "https://example.com/post-1",
    "title": "Interesting AI Post",
    "link": "https://example.com/post-1",
    "summary": "This post discusses large language models in detail.",
    "published_parsed": (2025, 1, 15, 10, 0, 0, 0, 0, 0),
}

_FAKE_PARSED = MagicMock()
_FAKE_PARSED.entries = [_FAKE_ENTRY := _FAKE_FEED_ENTRY]
_FAKE_PARSED.bozo = False


@pytest.fixture(name="seeded_feed", scope="function")
def seeded_feed_fixture(session: Session) -> Feed:
    _seed_settings(session)
    return _seed_feed(session)


def test_fetch_all_upserts_items(session: Session, seeded_feed: Feed) -> None:
    with patch("feedparser.parse", return_value=_FAKE_PARSED):
        statuses = fetch_all(session)
    session.commit()

    items = session.exec(select(NewsletterItem)).all()
    assert len(items) == 1
    assert items[0].title == "Interesting AI Post"
    assert items[0].status == NewsletterItemStatus.new
    assert seeded_feed.id in statuses


def test_fetch_all_deduplicates(session: Session, seeded_feed: Feed) -> None:
    with patch("feedparser.parse", return_value=_FAKE_PARSED):
        fetch_all(session)
        session.commit()
        fetch_all(session)
        session.commit()

    items = session.exec(select(NewsletterItem)).all()
    assert len(items) == 1  # second fetch is a no-op


def test_render_html_and_plaintext(session: Session, seeded_feed: Feed) -> None:
    now = datetime.now(UTC)
    item = NewsletterItem(
        feed_id=seeded_feed.id,
        external_id="test-1",
        title="Test Title",
        link="https://example.com",
        snippet="A snippet of text.",
        status=NewsletterItemStatus.new,
        created_at=now,
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    feeds_by_id = {seeded_feed.id: seeded_feed}
    html = render_html([item], feeds_by_id, {}, set(), {}, "Hello from Claude", now)
    text = render_plaintext([item], feeds_by_id, {}, set(), {}, "Hello from Claude", now)

    assert "Test Title" in html
    assert "Marginalia" in html
    assert "Hello from Claude" in html
    assert "Test Title" in text
    assert "Hello from Claude" in text


def test_runner_bootstrap(session: Session, seeded_feed: Feed) -> None:
    """First run with no existing items should create a bootstrap run (sent=False)."""
    with patch("feedparser.parse", return_value=_FAKE_PARSED):
        run = newsletter_run(session=session, send=False)

    assert run.sent is False
    assert run.intro_text == "seeded"


def test_runner_second_run_fetches_new_items(session: Session, seeded_feed: Feed) -> None:
    """After bootstrap, a second run fetches genuinely new items."""
    # Bootstrap
    with patch("feedparser.parse", return_value=_FAKE_PARSED):
        newsletter_run(session=session, send=False)

    # Second run — no new items since all are seeded as sent
    with patch("feedparser.parse", return_value=_FAKE_PARSED):
        run2 = newsletter_run(session=session, send=False)

    assert run2.items_count == 0
    assert run2.sent is False


def test_api_newsletter_items(client: TestClient, session: Session) -> None:
    """GET /api/newsletter/items returns items."""
    r = client.get("/api/newsletter/items")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_api_newsletter_runs(client: TestClient) -> None:
    r = client.get("/api/newsletter/runs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
