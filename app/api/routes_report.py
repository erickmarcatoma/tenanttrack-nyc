"""Building report: open violations with overdue flags + recent 311 complaints."""

import logging

from fastapi import APIRouter, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse

from app.api import templates
from app.data import hpd_client, nyc311_client
from app.i18n import normalize, translator
from app.rules.deadlines import class_label
from app.rules.overdue import evaluate_violation

router = APIRouter()
log = logging.getLogger(__name__)


@router.get("/building/{bin_}", response_class=HTMLResponse)
async def building_report(
    request: Request,
    bin_: str = Path(..., pattern=r"^\d{7}$"),
    bbl: str | None = Query(None, pattern=r"^\d{10}$"),
    lang: str = "en",
):
    lang = normalize(lang)
    try:
        violations = await hpd_client.get_open_violations(bin_)
        complaints = await nyc311_client.get_recent_complaints(bbl) if bbl else []
    except Exception as exc:
        log.exception("Open Data request failed")
        raise HTTPException(status_code=502, detail="NYC Open Data is unavailable") from exc

    rows = []
    for v in violations:
        ev = evaluate_violation(v)
        rows.append({"v": v, "eval": ev, "class_label": class_label(v.violation_class, lang)})
    rows.sort(key=lambda r: (r["eval"].status != "overdue", -r["eval"].days_overdue))

    return templates.TemplateResponse(
        request,
        "report.html",
        {
            "lang": lang,
            "t": translator(lang),
            "bin": bin_,
            "bbl": bbl,
            "rows": rows,
            "complaints": complaints,
        },
    )
