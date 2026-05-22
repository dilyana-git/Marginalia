# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the dev server
uv run uvicorn app.main:app --reload

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "describe change"

# Run all tests
uv run pytest tests/ -q

# Run a single test file or test
uv run pytest tests/test_works.py -q
uv run pytest tests/test_works.py::test_create_work -q

# Lint and format
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .

# Seed the database (after migrations)
uv run python scripts/seed.py

# Run the newsletter manually
uv run python scripts/run_newsletter.py
```

## Architecture

### Request flow

`app/main.py` → HTTP middleware (request-id, latency logging) → FastAPI router → route handler → `app/db.py:get_session()` → SQLModel session → response.

All routers are mounted under `/api`. Auth is handled by the `require_api_key` dependency in `app/deps.py` — it's a no-op when `APP_API_KEY` is unset, enforces header match otherwise.

### Layers

- **`app/models/`** — SQLModel table classes (ORM + schema in one). Enums all use `str, Enum` pattern (SQLModel compatibility; UP042 is suppressed in ruff config).
- **`app/schemas/`** — Pure Pydantic `BaseModel` classes for API request/response. Separate from models because some fields need different shapes (e.g. `tag_ids` assembled at read time, `authors` stored as JSON column).
- **`app/routes/`** — One file per resource; each file has its own `APIRouter`. Route handlers are thin: validate → DB op → return schema.
- **`app/services/seeding.py`** — Idempotent upsert of `seed.json` content. Keyed by name for regions, URL for feeds, (title, region_id, tier) for works. Called by `POST /api/import-export/import`.

### Newsletter pipeline

`app/newsletter/runner.py:run()` orchestrates in order:

1. **First-run bootstrap**: if no `NewsletterItem` rows exist, `fetcher.seed_as_sent()` marks all current feed entries as `sent` without emailing, creates a `NewsletterRun(sent=False, intro_text="seeded")`, and returns early.
2. **Fetch**: `fetcher.fetch_all()` reads all active feeds via feedparser, upserts new `NewsletterItem` rows with `status=new`.
3. **Cap**: items are capped per feed (`AppSettings.max_per_source`, default 6).
4. **Summarise**: `summarizer.summarize()` calls the Anthropic API (claude-haiku-4-5 by default). Gracefully returns `("", [], {})` when `ANTHROPIC_API_KEY` is unset.
5. **Render**: `renderer.render_html/render_plaintext()` produce the email body.
6. **Send**: `sender.send_email()` via SMTP. Port 465 uses SSL; 587 uses STARTTLS.
7. **Persist**: `NewsletterRun` row created; items marked `status=sent` with blurbs and highlight flags.

Preview HTML is always written to `out/preview.html` regardless of whether the email is sent.

### Data model key points

- `Work.authors` is stored as a JSON column (`sa_column=Column(JSON, nullable=False)`), not a relation. It's a `list[str]`.
- `WorkTag` and `JournalTag` are explicit link tables with `ondelete="CASCADE"`.
- `AppSettings` is a singleton — always `id=1`.
- `NewsletterItem` has a unique constraint on `(feed_id, external_id)`.
- All timestamps use `DateTime(timezone=True)` / `datetime` with UTC.

### Test isolation

Tests use an in-memory SQLite database with `StaticPool` (single shared connection). This is critical — without `StaticPool`, each `Session` gets its own empty database. The `engine`, `session`, and `client` fixtures in `tests/conftest.py` all share the same engine instance per test function.

The `import_export` tests do **not** use the `region` fixture (which inserts ordinal=1) because `seed.json` region "Artificial Intelligence" also has ordinal=1, causing a UNIQUE conflict.

### Schema/model separation gotcha

`app/schemas/journal.py` imports `from datetime import date as DateType` because the schema has a field named `date`; using `date` directly would shadow the type within the class namespace.

### Migrations

Only one migration exists (`0001_initial.py`), hand-written. `migrations/env.py` imports `app.models` (not individual models) to populate `SQLModel.metadata`, and sets `render_as_batch=True` for SQLite ALTER compatibility.

### Ruff config

Line length 100. Rules: E, F, I, UP, B. `B008` (function call in default arg) and `UP042` (str,Enum pattern) are suppressed. Use `# noqa: E501` for unavoidably long lines (e.g. error detail dicts).
