# Marginalia

A personal reading-tracker, reading-journal, and curated newsletter app for a single reader.

## Features

- **Reading tracker** — manage works (books, articles, papers, courses, videos) across regions, with status, tier, format, tags, and journal entries
- **Curated newsletter** — daily digest generated from RSS/Atom feeds, summarised by Claude (Anthropic API), sent via SMTP
- **Import/export** — seed the database from `seed.json`; export/replace data at any time
- **Single-user** — optional `X-Api-Key` header auth; no multi-tenancy

## Tech Stack

- Python 3.12, FastAPI, uvicorn
- SQLModel (Pydantic v2 + SQLAlchemy 2.x), SQLite, Alembic
- feedparser for RSS/Atom
- anthropic Python SDK (claude-haiku-4-5 by default)
- structlog for structured JSON logging
- uv for dependency management

## Quick Start

```bash
# Install uv (https://github.com/astral-sh/uv)
uv sync

# Copy and configure environment variables
cp .env.example .env
# edit .env — set ANTHROPIC_API_KEY, SMTP_*, MAIL_*, APP_API_KEY

# Run migrations
uv run alembic upgrade head

# Start the server
uv run uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

Seed the database with regions, works, feeds, and lists from `seed.json`:

```bash
curl -s -X POST http://localhost:8000/api/import-export/import \
  -H "Content-Type: application/json" \
  -d '{"mode": "merge"}'
```

## Environment Variables

See `.env.example` for all variables. Key ones:

| Variable | Purpose |
|---|---|
| `APP_API_KEY` | Optional API key for all endpoints (leave blank to disable auth) |
| `DATABASE_URL` | SQLite path (default: `sqlite:///./marginalia.db`) |
| `ANTHROPIC_API_KEY` | Required for newsletter summarisation |
| `SMTP_HOST` / `SMTP_PORT` | SMTP server for sending the newsletter |
| `SMTP_USER` / `SMTP_PASS` | SMTP credentials |
| `MAIL_FROM` / `MAIL_TO` | Sender and recipient addresses |

## Running the Newsletter

```bash
uv run python -c "
from app.db import get_session, create_db_and_tables
from app.newsletter.runner import run
create_db_and_tables()
with next(get_session()) as s:
    run(s, send=True)
"
```

A daily cron job is configured in `.github/workflows/daily.yml` to run at 06:00 UTC.

## Development

```bash
# Lint and format
uv run ruff check .
uv run ruff format .

# Tests
uv run pytest tests/ -q

# Create a new migration after model changes
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

## API Overview

All endpoints are under `/api`. Authenticated with `X-Api-Key` header when `APP_API_KEY` is set.

| Resource | Endpoints |
|---|---|
| Regions | `GET/POST /api/regions`, `GET/PUT/DELETE /api/regions/{id}` |
| Works | `GET/POST /api/works`, `GET/PUT/DELETE /api/works/{id}`, `PATCH /api/works/{id}/status`, `GET /api/works/{id}/journal` |
| Tags | `GET/POST /api/tags`, `GET/PUT/DELETE /api/tags/{id}` |
| Journal | `GET/POST /api/journal`, `GET/PUT/DELETE /api/journal/{id}` |
| Reading Lists | `GET/POST /api/lists`, `GET/PUT/DELETE /api/lists/{id}`, `POST/DELETE /api/lists/{id}/items` |
| Feeds | `GET/POST /api/feeds`, `GET/PUT/DELETE /api/feeds/{id}` |
| Newsletter | `POST /api/newsletter/run`, `GET /api/newsletter/runs`, `GET /api/newsletter/items` |
| Settings | `GET/PUT /api/settings` |
| Import/Export | `GET /api/import-export/export`, `POST /api/import-export/import` |
| Search | `GET /api/search?q=...` |

## Project Structure

```
app/
  config.py          # pydantic-settings; reads .env
  db.py              # SQLModel engine and session
  logging.py         # structlog configuration
  main.py            # FastAPI app, middleware, routers
  deps.py            # API key auth dependency
  models/            # SQLModel table models + enums
  schemas/           # Pydantic request/response schemas
  routes/            # FastAPI routers
  services/          # seeding, search
  newsletter/
    fetcher.py       # RSS/Atom feed fetching
    summarizer.py    # Claude API summarisation
    renderer.py      # HTML + plaintext email templates
    sender.py        # SMTP delivery
    runner.py        # Pipeline orchestration
migrations/          # Alembic migrations
tests/               # pytest suite
seed.json            # Seed data (regions, works, feeds, lists)
.github/workflows/   # Daily newsletter cron
```
