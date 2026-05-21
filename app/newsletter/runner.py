"""Orchestrate the newsletter pipeline."""

from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, func, select

from app.config import settings
from app.logging import get_logger
from app.models import AppSettings, Feed, NewsletterItem, NewsletterRun, Region
from app.models.enums import NewsletterItemStatus
from app.newsletter.fetcher import fetch_all, seed_as_sent
from app.newsletter.renderer import render_html, render_plaintext
from app.newsletter.summarizer import summarize

log = get_logger("newsletter.runner")

_PREVIEW_PATH = Path("out/preview.html")


def run(session: Session, send: bool = True) -> NewsletterRun:
    cfg = session.exec(select(AppSettings).where(AppSettings.id == 1)).first()
    reader_name = cfg.reader_name if cfg else "reader"
    reader_interests = cfg.reader_interests if cfg else ""
    model_name = cfg.model_name if cfg else "claude-haiku-4-5"
    max_per_source = cfg.max_per_source if cfg else 6
    recipient = (cfg.recipient_email if cfg else None) or settings.MAIL_TO

    log.info("newsletter run started", send=send)

    # First-run bootstrap: if no items exist, seed current as sent
    existing_count = session.exec(select(func.count(NewsletterItem.id))).one()
    if existing_count == 0:
        log.info("first run — seeding existing items as sent")
        seeded = seed_as_sent(session)
        session.commit()
        run_record = NewsletterRun(
            ran_at=datetime.now(UTC),
            items_count=seeded,
            sent=False,
            intro_text="seeded",
        )
        session.add(run_record)
        session.commit()
        session.refresh(run_record)
        log.info("bootstrap complete", seeded=seeded)
        return run_record

    # Fetch new items
    fetch_all(session)
    session.commit()

    # Collect items to include (status=new, capped per source)
    new_items_stmt = (
        select(NewsletterItem)
        .where(NewsletterItem.status == NewsletterItemStatus.new)
        .order_by(NewsletterItem.published_at.desc())  # type: ignore[attr-defined]
    )
    new_items = list(session.exec(new_items_stmt).all())

    # Cap per feed
    per_feed: dict[int, int] = {}
    capped: list[NewsletterItem] = []
    for item in new_items:
        count = per_feed.get(item.feed_id, 0)
        if count < max_per_source:
            capped.append(item)
            per_feed[item.feed_id] = count + 1

    log.info("items selected", total_new=len(new_items), after_cap=len(capped))

    if not capped:
        run_record = NewsletterRun(
            ran_at=datetime.now(UTC),
            items_count=0,
            sent=False,
            intro_text="no new items",
        )
        session.add(run_record)
        session.commit()
        session.refresh(run_record)
        return run_record

    # Summarise with Claude
    intro, highlight_ids, blurbs = summarize(
        items=capped,
        reader_name=reader_name,
        reader_interests=reader_interests,
        model_name=model_name,
        api_key=settings.ANTHROPIC_API_KEY,
    )
    highlight_id_set = set(highlight_ids)

    # Build lookup dicts for renderer
    feed_ids = {item.feed_id for item in capped}
    feeds_by_id: dict[int, Feed] = {
        f.id: f for f in session.exec(select(Feed).where(Feed.id.in_(feed_ids))).all()  # type: ignore[attr-defined]
    }
    region_ids = {f.region_id for f in feeds_by_id.values() if f.region_id}
    regions_by_id: dict[int, Region | None] = {
        r.id: r for r in session.exec(select(Region).where(Region.id.in_(region_ids))).all()  # type: ignore[attr-defined]
    }

    run_dt = datetime.now(UTC)
    _render_args = (capped, feeds_by_id, regions_by_id, highlight_id_set, blurbs, intro, run_dt)
    html = render_html(*_render_args)
    plaintext = render_plaintext(*_render_args)

    # Write preview
    _PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PREVIEW_PATH.write_text(html, encoding="utf-8")
    log.info("preview written", path=str(_PREVIEW_PATH))

    error_log: str | None = None
    actually_sent = False

    if send and recipient:
        from app.newsletter.sender import send_email

        subject = f"Marginalia — {run_dt.strftime('%-d %B %Y')}"
        try:
            send_email(subject, html, plaintext, recipient)
            actually_sent = True
        except Exception as exc:
            error_log = str(exc)
            log.error("email send failed", error=str(exc))
    elif send and not recipient:
        error_log = "No recipient configured (MAIL_TO or Settings.recipient_email)"
        log.warning(error_log)

    # Persist the run
    run_record = NewsletterRun(
        ran_at=run_dt,
        items_count=len(capped),
        sent=actually_sent,
        recipient=recipient if actually_sent else None,
        intro_text=intro or None,
        error_log=error_log,
    )
    session.add(run_record)
    session.flush()

    # Mark items + apply highlights / blurbs
    for item in capped:
        item.status = NewsletterItemStatus.sent
        item.sent_in_run_id = run_record.id
        item.is_highlight = item.id in highlight_id_set
        if item.id in blurbs:
            item.claude_blurb = blurbs[item.id]  # type: ignore[index]
        session.add(item)

    session.commit()
    session.refresh(run_record)

    log.info(
        "newsletter run complete",
        items=len(capped),
        sent=actually_sent,
        highlights=len(highlight_ids),
    )
    return run_record
