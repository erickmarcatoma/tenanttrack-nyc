"""Human-friendly, localized dates (no locale packages needed)."""

from datetime import date

MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"],
}


def format_date(d: date | None, lang: str = "en") -> str:
    """Jan 11, 2026 (en) / 11 de ene. de 2026 (es)."""
    if d is None:
        return ""
    if lang == "es":
        return f"{d.day} de {MONTHS['es'][d.month - 1]}. de {d.year}"
    return f"{MONTHS['en'][d.month - 1]} {d.day}, {d.year}"
