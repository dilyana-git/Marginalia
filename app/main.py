import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging import configure_logging, get_logger
from app.routes import (
    course,
    feeds,
    import_export,
    journal,
    lists,
    newsletter_route,
    regions,
    search,
    settings_route,
    tags,
    works,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    get_logger("startup").info("Marginalia starting", env=settings.APP_ENV)
    yield
    get_logger("shutdown").info("Marginalia stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Personal reading tracker, journal, and newsletter.",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_middleware(request: Request, call_next: object) -> Response:
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    response: Response = await call_next(request)  # type: ignore[operator]

    latency_ms = round((time.perf_counter() - start) * 1000, 1)
    get_logger("http").info(
        request.method,
        path=request.url.path,
        status=response.status_code,
        latency_ms=latency_ms,
    )
    response.headers["X-Request-Id"] = request_id
    return response


# --- API routers ---
_API = "/api"
app.include_router(regions.router, prefix=_API)
app.include_router(works.router, prefix=_API)
app.include_router(lists.router, prefix=_API)
app.include_router(journal.router, prefix=_API)
app.include_router(tags.router, prefix=_API)
app.include_router(feeds.router, prefix=_API)
app.include_router(newsletter_route.router, prefix=_API)
app.include_router(settings_route.router, prefix=_API)
app.include_router(search.router, prefix=_API)
app.include_router(import_export.router, prefix=_API)
app.include_router(course.router, prefix=_API)


# --- Meta endpoints ---
@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}


@app.get("/", tags=["meta"])
def banner() -> dict:
    return {"app": settings.APP_NAME, "version": "0.1.0", "env": settings.APP_ENV}


# --- RFC-7807 exception handler ---
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    get_logger("error").exception("unhandled error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred.",
        },
    )
