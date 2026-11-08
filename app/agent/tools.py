"""Tools the AI agent can call. Facts come from data clients and the rules engine, not the LLM."""

import re
from datetime import date
from typing import Any

from app.data import hpd_client
from app.i18n.dates import format_date
from app.rules.deadlines import class_label
from app.rules.overdue import RepairStatus, evaluate_violation


def _validate_bin(bin_: str) -> None:
    if not re.fullmatch(r"\d{7}", bin_):
        raise ValueError("BIN must be exactly 7 digits.")


async def lookup_violations(bin: str) -> list[dict]:
    _validate_bin(bin)
    violations = await hpd_client.get_open_violations(bin)
    return [
        {
            "id": v.violation_id,
            "apartment": v.apartment,
            "class": v.violation_class,
            "description": v.description,
            "issued": v.issued_date.isoformat() if v.issued_date else None,
            "correct_by": v.correct_by.isoformat() if v.correct_by else None,
        }
        for v in violations
    ]


async def check_deadlines(bin: str, today: date | None = None) -> list[dict]:
    """Fetch open violations for a BIN and evaluate their repair deadlines."""
    _validate_bin(bin)
    violations = await hpd_client.get_open_violations(bin)
    results = []
    for v in violations:
        ev = evaluate_violation(v, today=today)
        results.append(
            {
                "id": v.violation_id,
                "status": ev.status.value,
                "deadline": ev.deadline.isoformat() if ev.deadline else None,
                "days_overdue": ev.days_overdue,
            }
        )
    return results


async def draft_letter_for_building(
    bin: str,
    address: str = "",
    lang: str = "en",
    apartment: str = "",
    tenant_name: str = "",
    violation_ids: list[str] | None = None,
) -> str:
    """Fetch building violations and draft a letter using only HPD facts."""
    _validate_bin(bin)
    violations = await hpd_client.get_open_violations(bin)
    return draft_letter(
        address=address,
        violations=violations,
        lang=lang,
        apartment=apartment,
        tenant_name=tenant_name,
        violation_ids=set(violation_ids) if violation_ids is not None else None,
    )


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "lookup_violations",
        "description": "Look up open HPD housing violations for a NYC building.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "bin": {
                    "type": "STRING",
                    "description": (
                        "The building's 7-digit NYC Building Identification Number (BIN)."
                    ),
                }
            },
            "required": ["bin"],
        },
    },
    {
        "name": "check_deadlines",
        "description": (
            "Fetch open HPD violations for a building and evaluate their repair deadlines."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "bin": {
                    "type": "STRING",
                    "description": (
                        "The building's 7-digit NYC Building Identification Number (BIN)."
                    ),
                }
            },
            "required": ["bin"],
        },
    },
    {
        "name": "draft_letter",
        "description": (
            "Draft a tenant letter about open HPD violations. Include only selected "
            "violation IDs when provided; otherwise include overdue violations."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "bin": {
                    "type": "STRING",
                    "description": (
                        "The building's 7-digit NYC Building Identification Number (BIN)."
                    ),
                },
                "address": {
                    "type": "STRING",
                    "description": "Building street address, if known.",
                },
                "lang": {
                    "type": "STRING",
                    "enum": ["en", "es"],
                    "description": "Letter language.",
                },
                "apartment": {
                    "type": "STRING",
                    "description": "Tenant's apartment number, if provided.",
                },
                "tenant_name": {
                    "type": "STRING",
                    "description": "Tenant's name, if provided.",
                },
                "violation_ids": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": (
                        "Optional HPD violation IDs to include. Omit to include overdue "
                        "violations."
                    ),
                },
            },
            "required": ["bin"],
        },
    },
]


LETTER_TEMPLATES = {
    "en": {
        "body": (
            "{today}\n\n"
            "To: Owner / Managing Agent\n"
            "Re: Open HPD violations at {address}{apt}\n\n"
            "Dear Owner or Managing Agent,\n\n"
            "I am a tenant at {address}{apt}. The NYC Department of Housing Preservation "
            "and Development (HPD) has issued the following open violations for this "
            "building, which still need to be repaired:\n\n"
            "{items}\n\n"
            "Please complete these repairs as soon as possible and let me know when the "
            "work will be scheduled. If the repairs are not made, I will file a complaint "
            "with 311 / HPD.\n\n"
            "Sincerely,\n{tenant_name}"
        ),
        "item": "- {vnum}{id} (Class {cls}, {label}){apt}: {desc}. {due}",
        "vnum": "Violation #",
        "overdue": "Legal correction date was {date} ({n} days overdue).",
        "due": "Must be corrected by {date}.",
        "no_date": "Correction date not listed.",
        "apt": ", apt. {apt}",
        "item_apt": ", apt. {apt}",
        "none": "- (No overdue violations selected.)",
        "name": "[Your name]",
    },
    "es": {
        "body": (
            "{today}\n\n"
            "Para: Propietario / Agente administrador\n"
            "Asunto: Violaciones abiertas de HPD en {address}{apt}\n\n"
            "Estimado propietario o agente administrador:\n\n"
            "Soy inquilino/a en {address}{apt}. El Departamento de Preservación y "
            "Desarrollo de la Vivienda de NYC (HPD) ha emitido las siguientes violaciones "
            "abiertas para este edificio, que todavía deben repararse:\n\n"
            "{items}\n\n"
            "Por favor, complete estas reparaciones lo antes posible e infórmeme cuándo "
            "se programará el trabajo. Si no se hacen las reparaciones, presentaré una "
            "queja ante el 311 / HPD.\n\n"
            "Atentamente,\n{tenant_name}"
        ),
        "item": "- {vnum}{id} (Clase {cls}, {label}){apt}: {desc}. {due}",
        "vnum": "Violación n.º ",
        "overdue": "La fecha legal de corrección fue el {date} ({n} días de retraso).",
        "due": "Debe corregirse antes del {date}.",
        "no_date": "Fecha de corrección no indicada.",
        "apt": ", apto. {apt}",
        "item_apt": ", apto. {apt}",
        "none": "- (No se seleccionaron violaciones vencidas.)",
        "name": "[Su nombre]",
    },
}


def draft_letter(
    address: str,
    violations: list,
    lang: str = "en",
    apartment: str = "",
    tenant_name: str = "",
    violation_ids: set[str] | None = None,
    today: date | None = None,
) -> str:
    """Draft a landlord letter.

    By default it lists only overdue violations. Pass violation_ids to list specific ones.
    Template-based so facts are always correct; the LLM can polish wording later.
    """
    lang = lang if lang in LETTER_TEMPLATES else "en"
    tpl = LETTER_TEMPLATES[lang]
    today = today or date.today()

    lines = []
    for v in violations:
        ev = evaluate_violation(v, today=today)
        if violation_ids is not None:
            if v.violation_id not in violation_ids:
                continue
        elif ev.status != RepairStatus.OVERDUE:
            continue

        if ev.status == RepairStatus.OVERDUE:
            due = tpl["overdue"].format(date=format_date(ev.deadline, lang), n=ev.days_overdue)
        elif ev.deadline:
            due = tpl["due"].format(date=format_date(ev.deadline, lang))
        else:
            due = tpl["no_date"]

        lines.append(
            tpl["item"].format(
                vnum=tpl["vnum"],
                id=v.violation_id,
                cls=v.violation_class,
                label=class_label(v.violation_class, lang),
                apt=tpl["item_apt"].format(apt=v.apartment) if v.apartment else "",
                desc=v.description.rstrip("."),
                due=due,
            )
        )

    return tpl["body"].format(
        today=format_date(today, lang),
        address=address or "[Building address]",
        apt=tpl["apt"].format(apt=apartment) if apartment else "",
        items="\n".join(lines) or tpl["none"],
        tenant_name=tenant_name or tpl["name"],
    )
