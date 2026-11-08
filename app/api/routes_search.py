"""Home page and address lookup."""

import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api import templates
from app.data import geoclient
from app.i18n import normalize, translator
from app.logging_config import log_upstream_error

router = APIRouter()
log = logging.getLogger(__name__)


@router.get("/", response_class=HTMLResponse)
def home(request: Request, lang: str = "en", error: bool = False):
    lang = normalize(lang)
    return templates.TemplateResponse(
        request,
        "index.html",
        {"lang": lang, "t": translator(lang), "error": error},
    )


@router.get("/search")
async def search(address: str = Query(..., min_length=3, max_length=200), lang: str = "en"):
    lang = normalize(lang)
    try:
        results = await geoclient.search(address)
    except Exception as exc:
        log_upstream_error(log, "NYC Geoclient", exc)
        results = []
    if not results:
        return RedirectResponse(f"/?lang={lang}&error=1", status_code=303)
    loc = results[0]
    display = ", ".join(p for p in (loc.address.title(), loc.borough.title()) if p)
    query = urlencode({"bbl": loc.bbl, "address": display, "lang": lang})
    return RedirectResponse(f"/building/{loc.bin}?{query}", status_code=303)
