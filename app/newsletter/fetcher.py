"""Fetch active RSS/Atom feeds and upsert NewsletterItems."""

from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime

import feedparser
from sqlmodel import Session, select

from app.logging import get_logger
from app.models import AppSettings, Feed, NewsletterItem
from app.models.enums import NewsletterItemStatus

log = get_logger("newsletter.fetcher")

_MAX_SNIPPET_LEN = 500
_PER_FEED_SAFETY_CAP = 50  # hard cap regardless of settings


def _parse_dt(entry: dict) -> datetime | None:
    for key in ("published", "updated"):
        val = entry.get(f"{key}_parsed") or entry.get(key)
        if val is None:
            continue
        if hasattr(val, "tm_year"):
            try:
                return datetime(*val[:6], tzinfo=UTC)
            except Exception:
                continue
        if isinstance(val, str):
            try:
                dt = parsedate_to_datetime(val)
                return dt.astimezone(UTC)
            except Exception:
                continue
    return None


def _snippet(entry: dict) -> str:
    for key in ("summary", "content", "description"):
        val = entry.get(key)
        if val is None:
            continue
        if isinstance(val, list):
            val = val[0].get("value", "") if val else ""
        text = val.replace("\n", " ").strip()
        if text:
            return text[:_MAX_SNIPPET_LEN]
    return entry.get("title", "")[:_MAX_SNIPPET_LEN]


def fetch_all(session: Session) -> dict[int, str]:
    """Fetch all active feeds; return {feed_id: status_string}."""
    cfg = session.exec(select(AppSettings).where(AppSettings.id == 1)).first()
    lookback_days = cfg.lookback_days if cfg else 7
    max_per_source = min(cfg.max_per_source if cfg else 6, _PER_FEED_SAFETY_CAP)
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)

    feeds = session.exec(select(Feed).where(Feed.active == True)).all()  # noqa: E712
    statuses: dict[int, str] = {}

    for feed in feeds:
        try:
            parsed = feedparser.parse(feed.url)
            new_count = 0
            for entry in parsed.entries[:max_per_source]:
                ext_id = entry.get("id") or entry.get("link") or entry.get("title", "")
                if not ext_id:
                    continue

                published = _parse_dt(entry)
                if published and published < cutoff:
                    continue

                existing = session.exec(
                    select(NewsletterItem).where(
                        NewsletterItem.feed_id == feed.id,
                        NewsletterItem.external_id == ext_id,
                    )
                ).first()
                if existing:
                    continue

                item = NewsletterItem(
                    feed_id=feed.id,
                    external_id=ext_id,
                    title=entry.get("title", "(no title)"),
                    link=entry.get("link"),
                    published_at=published,
                    snippet=_snippet(entry),
                    status=NewsletterItemStatus.new,
                    created_at=datetime.now(UTC),
                )
                session.add(item)
                new_count += 1

            status = f"ok: {new_count} new"
            statuses[feed.id] = status
            feed.last_status = status
            log.info("fetched feed", name=feed.name, new=new_count)

        except Exception as exc:
            status = f"error: {exc}"
            statuses[feed.id] = status
            feed.last_status = status
            log.warning("feed fetch failed", name=feed.name, error=str(exc))

        feed.last_fetched_at = datetime.now(UTC)
        session.add(feed)

    session.flush()
    return statuses


def seed_as_sent(session: Session) -> int:
    """First-run bootstrap: mark all current feed items as sent without emailing."""
    feeds = session.exec(select(Feed).where(Feed.active == True)).all()  # noqa: E712
    count = 0
    for feed in feeds:
        try:
            parsed = feedparser.parse(feed.url)
            for entry in parsed.entries[:_PER_FEED_SAFETY_CAP]:
                ext_id = entry.get("id") or entry.get("link") or entry.get("title", "")
                if not ext_id:
                    continue
                existing = session.exec(
                    select(NewsletterItem).where(
                        NewsletterItem.feed_id == feed.id,
                        NewsletterItem.external_id == ext_id,
                    )
                ).first()
                if existing:
                    continue
                item = NewsletterItem(
                    feed_id=feed.id,
                    external_id=ext_id,
                    title=entry.get("title", "(no title)"),
                    link=entry.get("link"),
                    published_at=_parse_dt(entry),
                    snippet=_snippet(entry),
                    status=NewsletterItemStatus.sent,
                    created_at=datetime.now(UTC),
                )
                session.add(item)
                count += 1
        except Exception as exc:
            log.warning("seed_as_sent feed failed", name=feed.name, error=str(exc))
    session.flush()
    return count
