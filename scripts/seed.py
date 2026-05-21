#!/usr/bin/env python
"""CLI: load or refresh seed.json into the database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from sqlmodel import Session

from app.db import create_db_and_tables, engine
from app.logging import configure_logging, get_logger
from app.services.seeding import run_seed

configure_logging()
log = get_logger("seed")


def main() -> None:
    log.info("running Alembic migrations")
    # Ensure tables exist (idempotent; Alembic is the real migration path)
    create_db_and_tables()

    log.info("loading seed.json")
    with Session(engine) as session:
        counts = run_seed(session)

    log.info(
        "seed complete",
        regions=counts["regions"],
        works=counts["works"],
        articles=counts["articles"],
        feeds=counts["feeds"],
    )


if __name__ == "__main__":
    main()
