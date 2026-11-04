"""Building report and landlord letter pages."""

import logging
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse

from app.agent.tools import draft_letter
from app.api import templates
from app.data import hpd_client, nyc311_client
from app.i18n import normalize, translator
from app.logging_config import log_upstream_error
from app.rules.deadlines import class_label
from app.rules.overdue import RepairStatus, evaluate_violation

router = APIRouter()
log = logging.getLogger(__name__)

BIN = Path(..., pattern=r"^\d{7}$")


async def _violations(bin_: str):
    try:
        return await hpd_client.get_open_violations(bin_)
    except Exception as exc:
        log_upstream_error(
            log, hpd_client.DATASET_NAME, exc, dataset_id=hpd_client.DATASET_ID
        )
        raise HTTPException(status_code=502, detail="NYC Open Data is unavailable") from exc


def report_url(bin_: str, bbl: str | None, address: str, lang: str) -> str:
    params = {k: v for k, v in {"bbl": bbl, "address": address, "lang": lang}.items() if v}
    return f"/building/{bin_}?{urlencode(params)}"


def letter_url(
    bin_: str, bbl: str | None, address: str, lang: str, violation: str | None = None
) -> str:
    params = {k: v for k, v in {"bbl": bbl, "address": address, "lang": lang}.items() if v}
    if violation:
        params["violation"] = violation
    return f"/building/{bin_}/letter?{urlencode(params)}"


@router.get("/building/{bin_}", response_class=HTMLResponse)
async def building_report(
    request: Request,
    bin_: str = BIN,
    bbl: str | None = Query(None, pattern=r"^\d{10}$"),
    address: str = Query("", max_length=200),
    lang: str = "en",
):
    lang = normalize(lang)
    t = translator(lang)
    violations = await _violations(bin_)
    complaints = []
    if bbl:
        try:
            complaints = await nyc311_client.get_recent_complaints(bbl)
        except Exception as exc:
            log_upstream_error(
                log, nyc311_client.DATASET_NAME, exc, dataset_id=nyc311_client.DATASET_ID
            )

    rows = []
    for v in violations:
        ev = evaluate_violation(v)
        rows.append(
            {
                "v": v,
                "eval": ev,
                "class_label": class_label(v.violation_class, lang),
                "letter_url": letter_url(bin_, bbl, address, lang, v.violation_id),
            }
        )
    rows.sort(key=lambda r: (r["eval"].status != RepairStatus.OVERDUE, -r["eval"].days_overdue))

    overdue = sum(1 for r in rows if r["eval"].status == RepairStatus.OVERDUE)
    if overdue == 1:
        summary = t("summary_overdue_one")
    else:
        summary = t("summary_overdue_many").replace("{n}", str(overdue))

    return templates.TemplateResponse(
        request,
        "report.html",
        {
            "lang": lang,
            "t": t,
            "bin": bin_,
            "bbl": bbl,
            "address": address,
            "rows": rows,
            "complaints": complaints,
            "overdue": overdue,
            "summary": summary,
            "letter_url": letter_url(bin_, bbl, address, lang),
        },
    )


@router.get("/building/{bin_}/letter", response_class=HTMLResponse)
async def letter_page(
    request: Request,
    bin_: str = BIN,
    bbl: str | None = Query(None, pattern=r"^\d{10}$"),
    address: str = Query("", max_length=200),
    apartment: str = Query("", max_length=20),
    name: str = Query("", max_length=100),
    violation: str | None = Query(None, pattern=r"^\d{1,12}$"),
    lang: str = "en",
):
    lang = normalize(lang)
    violations = await _violations(bin_)
    letter = draft_letter(
        address=address,
        violations=violations,
        lang=lang,
        apartment=apartment,
        tenant_name=name,
        violation_ids={violation} if violation else None,
    )
    return templates.TemplateResponse(
        request,
        "letter.html",
        {
            "lang": lang,
            "t": translator(lang),
            "bin": bin_,
            "bbl": bbl,
            "address": address,
            "apartment": apartment,
            "name": name,
            "violation": violation,
            "letter": letter,
            "report_url": report_url(bin_, bbl, address, lang),
        },
    )
