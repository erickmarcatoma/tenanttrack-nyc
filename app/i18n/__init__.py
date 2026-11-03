"""Tiny translation helper backed by en.json / es.json."""

import json
from functools import lru_cache
from pathlib import Path

SUPPORTED = ("en", "es")
DEFAULT = "en"


@lru_cache
def _load(lang: str) -> dict[str, str]:
    path = Path(__file__).parent / f"{lang}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(lang: str | None) -> str:
    return lang if lang in SUPPORTED else DEFAULT


def translator(lang: str | None):
    strings = _load(normalize(lang))
    fallback = _load(DEFAULT)

    def t(key: str) -> str:
        return strings.get(key) or fallback.get(key) or key

    return t
