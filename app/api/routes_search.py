"""Home page and address lookup."""

import logging

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api import templates
from app.data import geoclient
from app.i18n import normalize, translator

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
    except Exception:
        log.exception("Geoclient lookup failed")
        results = []
    if not results:
        return RedirectResponse(f"/?lang={lang}&error=1", status_code=303)
    loc = results[0]
    return RedirectResponse(f"/building/{loc.bin}?bbl={loc.bbl}&lang={lang}", status_code=303)
