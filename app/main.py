"""FastAPI entry point."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import routes_agent, routes_alerts, routes_report, routes_search
from app.config import get_settings

BASE_DIR = Path(__file__).parent

settings = get_settings()
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="TenantTrack NYC", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

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
