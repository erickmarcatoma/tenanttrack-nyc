"""Tools the AI agent can call. Facts come from data clients and the rules engine, not the LLM."""

from datetime import date

from app.data import hpd_client
from app.rules.deadlines import class_label
from app.rules.overdue import RepairStatus, evaluate_violation


async def lookup_violations(bin_: str) -> list[dict]:
    violations = await hpd_client.get_open_violations(bin_)
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


def check_deadlines(violations: list, today: date | None = None) -> list[dict]:
    """Run the rules engine over hpd_client.Violation objects."""
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


LETTER_TEMPLATES = {
    "en": (
        "To the owner/manager of {address}:\n\n"
        "I am a tenant at {address}{apt}. HPD has issued the following open violations "
        "for this building that are past their legal correction date:\n\n"
        "{items}\n\n"
        "Please complete these repairs promptly. If they are not fixed, "
        "I will file a complaint with 311/HPD.\n\n"
        "Sincerely,\n{tenant_name}"
    ),
    "es": (
        "Al propietario/administrador de {address}:\n\n"
        "Soy inquilino/a en {address}{apt}. HPD ha emitido las siguientes violaciones abiertas "
        "para este edificio que ya pasaron su fecha legal de corrección:\n\n"
        "{items}\n\n"
        "Por favor, complete estas reparaciones pronto. Si no se corrigen, "
        "presentaré una queja ante 311/HPD.\n\n"
        "Atentamente,\n{tenant_name}"
    ),
}


def draft_letter(
    address: str,
    violations: list,
    lang: str = "en",
    apartment: str = "",
    tenant_name: str = "",
    today: date | None = None,
) -> str:
    """Draft a landlord letter listing overdue violations. Template-based; the LLM can polish it."""
    lang = lang if lang in LETTER_TEMPLATES else "en"
    lines = []
    for v in violations:
        ev = evaluate_violation(v, today=today)
        if ev.status != RepairStatus.OVERDUE:
            continue
        label = class_label(v.violation_class, lang)
        lines.append(f"- #{v.violation_id} ({label}): {v.description}")
    items = "\n".join(lines) or "-"
    apt = f", apt. {apartment}" if apartment else ""
    return LETTER_TEMPLATES[lang].format(
        address=address,
        apt=apt,
        items=items,
        tenant_name=tenant_name or "[Your name]",
    )
