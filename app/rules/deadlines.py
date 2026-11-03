"""Legal correction periods by HPD violation class.

TODO: confirm these against current HPD rules before launch (see PLAN.md, Phase 2).
Some violation types have their own periods (e.g. lead paint, window guards);
when the dataset gives a correct-by date, that date always wins.
"""

from datetime import date, timedelta

# Days allowed to correct, counted from the date the notice of violation was issued.
CORRECTION_DAYS: dict[str, int] = {
    "A": 90,  # non-hazardous
    "B": 30,  # hazardous
    "C": 1,  # immediately hazardous (24 hours)
}

CLASS_LABELS: dict[str, dict[str, str]] = {
    "A": {"en": "Non-hazardous", "es": "No peligrosa"},
    "B": {"en": "Hazardous", "es": "Peligrosa"},
    "C": {"en": "Immediately hazardous", "es": "Inmediatamente peligrosa"},
    "I": {"en": "Information / order", "es": "Información / orden"},
}


def deadline_for(
    violation_class: str,
    issued_date: date | None,
    correct_by: date | None = None,
) -> date | None:
    """Return the repair deadline. Prefer the dataset's correct-by date."""
    if correct_by is not None:
        return correct_by
    days = CORRECTION_DAYS.get(violation_class.upper())
    if days is None or issued_date is None:
        return None
    return issued_date + timedelta(days=days)


def class_label(violation_class: str, lang: str = "en") -> str:
    labels = CLASS_LABELS.get(violation_class.upper())
    if labels is None:
        return violation_class
    return labels.get(lang, labels["en"])
