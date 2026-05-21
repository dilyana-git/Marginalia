"""Idempotent seed loader for seed.json."""

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

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

SEED_PATH = Path(__file__).parents[2] / "seed.json"

SYSTEM_LIST_NAMES = ["Currently Reading", "Want to Read", "Finished", "Abandoned"]


def load_seed(path: Path = SEED_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _upsert_region(session: Session, data: dict) -> Region:
    stmt = select(Region).where(Region.name == data["name"])
    region = session.exec(stmt).first()
    if region is None:
        region = Region(
            ordinal=data["ordinal"],
            name=data["name"],
            qualifier=data.get("qualifier"),
            why=data["why"],
            rank_note=data.get("rank_note"),
            anchor=data.get("anchor"),
            created_at=_now(),
            updated_at=_now(),
        )
        session.add(region)
    else:
        region.ordinal = data["ordinal"]
        region.qualifier = data.get("qualifier")
        region.why = data["why"]
        region.rank_note = data.get("rank_note")
        region.anchor = data.get("anchor")
        region.updated_at = _now()
    session.flush()
    return region


def _upsert_work_from_seed(
    session: Session,
    item: dict,
    region_id: int | None,
    *,
    key_by_url: bool = False,
) -> Work:
    if key_by_url and item.get("url"):
        stmt = select(Work).where(Work.url == item["url"])
    else:
        stmt = select(Work).where(
            Work.title == item["title"],
            Work.region_id == region_id,
            Work.tier == item.get("tier", WorkTier.unranked),
        )

    work = session.exec(stmt).first()

    fmt = WorkFormat(item["format"]) if item.get("format") else WorkFormat.other
    tier = WorkTier(item["tier"]) if item.get("tier") else WorkTier.unranked
    origin = SeedOrigin(item.get("seed_origin", "manual"))

    if work is None:
        work = Work(
            title=item["title"],
            subtitle=item.get("subtitle"),
            authors=item.get("authors", []),
            year=item.get("year"),
            format=fmt,
            region_id=region_id,
            tier=tier,
            source_name=item.get("source_name"),
            url=item.get("url"),
            description=item.get("description"),
            is_start_here=item.get("is_start_here", False),
            seed_origin=origin,
            date_added=_now(),
            created_at=_now(),
            updated_at=_now(),
        )
        session.add(work)
    else:
        work.subtitle = item.get("subtitle")
        work.authors = item.get("authors", [])
        work.year = item.get("year")
        work.format = fmt
        work.region_id = region_id
        work.tier = tier
        work.source_name = item.get("source_name")
        work.url = item.get("url")
        work.description = item.get("description")
        work.is_start_here = item.get("is_start_here", False)
        work.seed_origin = origin
        work.updated_at = _now()

    session.flush()
    return work


def _upsert_feed(session: Session, item: dict, region_id: int | None) -> Feed:
    stmt = select(Feed).where(Feed.url == item["url"])
    feed = session.exec(stmt).first()

    ftype = FeedType(item["type"])
    fkind = FeedKind(item["kind"])
    origin = SeedOrigin(item.get("seed_origin", "manual"))

    if feed is None:
        feed = Feed(
            name=item["name"],
            type=ftype,
            kind=fkind,
            url=item["url"],
            region_id=region_id,
            notes=item.get("notes"),
            seed_origin=origin,
            active=True,
            created_at=_now(),
            updated_at=_now(),
        )
        session.add(feed)
    else:
        feed.name = item["name"]
        feed.type = ftype
        feed.kind = fkind
        feed.region_id = region_id
        feed.notes = item.get("notes")
        feed.seed_origin = origin
        feed.updated_at = _now()

    session.flush()
    return feed


def _upsert_system_list(session: Session, name: str) -> ReadingList:
    stmt = select(ReadingList).where(ReadingList.name == name, ReadingList.is_system == True)  # noqa: E712
    lst = session.exec(stmt).first()
    if lst is None:
        lst = ReadingList(name=name, is_system=True, created_at=_now())
        session.add(lst)
        session.flush()
    return lst


def _upsert_settings(session: Session, reader: dict) -> AppSettings:
    stmt = select(AppSettings).where(AppSettings.id == 1)
    s = session.exec(stmt).first()
    if s is None:
        s = AppSettings(
            id=1,
            reader_name=reader.get("name", ""),
            reader_interests=reader.get("interests", ""),
            timezone=reader.get("timezone", "Europe/Sofia"),
        )
        session.add(s)
    else:
        s.reader_name = reader.get("name", s.reader_name)
        s.reader_interests = reader.get("interests", s.reader_interests)
        s.timezone = reader.get("timezone", s.timezone)
    session.flush()
    return s


def run_seed(session: Session, path: Path = SEED_PATH) -> dict:
    data = load_seed(path)

    # Settings
    _upsert_settings(session, data.get("reader", {}))

    # System reading lists
    for name in SYSTEM_LIST_NAMES:
        _upsert_system_list(session, name)

    region_counts = {"regions": 0, "works": 0, "articles": 0, "feeds": 0}

    for region_data in data.get("regions", []):
        region = _upsert_region(session, region_data)
        region_counts["regions"] += 1

        # Per-region system list
        _upsert_system_list(session, region_data["name"])

        # Course books
        for work_item in region_data.get("works", []):
            _upsert_work_from_seed(session, work_item, region.id, key_by_url=False)
            region_counts["works"] += 1

        # Articles / essays (keyed by URL when available)
        for article_item in region_data.get("articles", []):
            _upsert_work_from_seed(session, article_item, region.id, key_by_url=True)
            region_counts["articles"] += 1

        # Feeds (primary + extra)
        for feed_item in region_data.get("feeds", []) + region_data.get("extra_feeds", []):
            _upsert_feed(session, feed_item, region.id)
            region_counts["feeds"] += 1

    # Cross-cutting feeds (no region)
    for feed_item in data.get("cross_cutting_feeds", []):
        _upsert_feed(session, feed_item, None)
        region_counts["feeds"] += 1

    session.commit()
    return region_counts
