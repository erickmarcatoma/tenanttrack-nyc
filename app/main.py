"""FastAPI entry point."""

import logging
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.api import routes_agent, routes_alerts, routes_report, routes_search
from app.config import get_settings
from app.logging_config import configure_logging

BASE_DIR = Path(__file__).parent

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title="TenantTrack NYC", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

request_log = logging.getLogger("app.request")


@app.middleware("http")
async def log_request(request: Request, call_next: RequestResponseEndpoint) -> Response:
    started_at = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        request_log.info(
            "Request completed",
            extra={
                "event": "http_request",
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            },
        )


app.include_router(routes_search.router)
app.include_router(routes_report.router)
app.include_router(routes_agent.router)
app.include_router(routes_alerts.router)


@app.get("/service-worker.js", include_in_schema=False)
def service_worker() -> FileResponse:
    # Served from the root so it can control every page.
    return FileResponse(BASE_DIR / "static" / "service-worker.js", media_type="text/javascript")


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    return {"status": "ok"}
