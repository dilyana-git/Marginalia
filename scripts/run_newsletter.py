#!/usr/bin/env python
"""CLI: fetch feeds, summarise, render, and optionally send today's newsletter."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from sqlmodel import Session

from app.db import engine
from app.logging import configure_logging, get_logger
from app.newsletter.runner import run as newsletter_run

configure_logging()
log = get_logger("run_newsletter")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Marginalia newsletter pipeline.")
    parser.add_argument(
        "--no-send",
        action="store_true",
        help="Fetch and render but do not send the email.",
    )
    args = parser.parse_args()

    send = not args.no_send

    with Session(engine) as session:
        run_record = newsletter_run(session=session, send=send)

    log.info(
        "done",
        run_id=run_record.id,
        items=run_record.items_count,
        sent=run_record.sent,
    )
    if run_record.error_log:
        log.warning("run had errors", error=run_record.error_log)
        sys.exit(1)


if __name__ == "__main__":
    main()
