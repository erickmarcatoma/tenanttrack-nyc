"""Gemini-backed agent that can call TenantTrack data tools."""

import logging
import re
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from app.agent import tools
from app.config import get_settings

PROMPTS_DIR = Path(__file__).parent / "prompts"
MAX_STEPS = 6
API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
TOOL_REGISTRY = {
    "lookup_violations": tools.lookup_violations,
    "check_deadlines": tools.check_deadlines,
    "draft_letter": tools.draft_letter_for_building,
}

log = logging.getLogger(__name__)

DATE_PATTERN = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
    r"[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b"
    r"|\b\d{1,2}\s+de\s+(?:ene|feb|mar|abr|may|jun|jul|ago|sept?|oct|nov|dic)"
    r"\.?\s+de\s+\d{4}\b",
    re.IGNORECASE,
)
ENGLISH_MONTHS = {
    name.casefold(): index
    for index, names in enumerate(
        [
            ("jan", "january"),
            ("feb", "february"),
            ("mar", "march"),
            ("apr", "april"),
            ("may",),
            ("jun", "june"),
            ("jul", "july"),
            ("aug", "august"),
            ("sep", "sept", "september"),
            ("oct", "october"),
            ("nov", "november"),
            ("dec", "december"),
        ],
        start=1,
    )
    for name in names
}
SPANISH_MONTHS = {
    name: index
    for index, names in enumerate(
        [
            ("ene", "enero"),
            ("feb", "febrero"),
            ("mar", "marzo"),
            ("abr", "abril"),
            ("may", "mayo"),
            ("jun", "junio"),
            ("jul", "julio"),
            ("ago", "agosto"),
            ("sept", "sep", "septiembre", "setiembre"),
            ("oct", "octubre"),
            ("nov", "noviembre"),
            ("dic", "diciembre"),
        ],
        start=1,
    )
    for name in names
}
LEGAL_ADVICE_PATTERNS = (
    re.compile(
        r"\b(?:should i sue|can i sue|do i have a case|"
        r"what are my legal rights|can i (?:legally )?withhold (?:my )?rent|"
        r"can i stop paying rent|should i take legal action|"
        r"should i file (?:a )?(?:lawsuit|suit)|do i need a lawyer|"
        r"i need legal advice)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:debo demandar|puedo demandar|tengo un caso|"
        r"cu[aá]les son mis derechos legales|"
        r"puedo retener (?:el|la) (?:alquiler|renta)|"
        r"puedo dejar de pagar (?:el )?(?:alquiler|renta))\b",
        re.IGNORECASE,
    ),
)
LEGAL_ADVICE_REFUSAL = {
    "en": (
        "I can’t provide legal advice. For help with your situation, contact a "
        "tenant legal-aid organization or call 311."
    ),
    "es": (
        "No puedo ofrecer asesoría legal. Para recibir ayuda con su situación, "
        "comuníquese con una organización de asistencia legal para inquilinos o llame al 311."
    ),
}
UNVERIFIED_DATE_RESPONSE = {
    "en": "I can’t verify that date from the HPD records available here.",
    "es": "No puedo verificar esa fecha con los registros de HPD disponibles aquí.",
}
UNVERIFIED_CLASS_RESPONSE = {
    "en": (
        "I can only describe HPD classes using their official labels: Class A "
        '"Non-hazardous," Class B "Hazardous," and Class C "Immediately hazardous."'
    ),
    "es": (
        "Solo puedo describir las clases de HPD con sus nombres oficiales: Clase A "
        '"No peligrosa," Clase B "Peligrosa" y Clase C "Inmediatamente peligrosa."'
    ),
}


def system_prompt(lang: str = "en") -> str:
    name = "es.md" if lang == "es" else "en.md"
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _parse_dates(value: str) -> set[date]:
    value = value.strip().rstrip(".")
    try:
        return {date.fromisoformat(value)}
    except ValueError:
        pass

    numeric = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", value)
    if numeric:
        year = int(numeric.group(3))
        if year < 100:
            year += 2000 if year <= 68 else 1900
        candidates = set()
        for month, day in (
            (int(numeric.group(1)), int(numeric.group(2))),
            (int(numeric.group(2)), int(numeric.group(1))),
        ):
            try:
                candidates.add(date(year, month, day))
            except ValueError:
                continue
        return candidates

    english = re.fullmatch(
        r"([A-Za-z]+)\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})",
        value,
        re.IGNORECASE,
    )
    if english:
        month = ENGLISH_MONTHS.get(english.group(1).casefold())
        if month:
            try:
                return {date(int(english.group(3)), month, int(english.group(2)))}
            except ValueError:
                return set()

    spanish = re.fullmatch(
        r"(\d{1,2})\s+de\s+([A-Za-z]+)\.?\s+de\s+(\d{4})", value, re.IGNORECASE
    )
    if spanish:
        month = SPANISH_MONTHS.get(spanish.group(2).casefold())
        if month:
            try:
                return {date(int(spanish.group(3)), month, int(spanish.group(1)))}
            except ValueError:
                return set()
    return set()


def _dates_in(value: Any) -> set[date]:
    if isinstance(value, dict):
        return set().union(*(_dates_in(item) for item in value.values()))
    if isinstance(value, (list, tuple)):
        return set().union(*(_dates_in(item) for item in value))
    if isinstance(value, str):
        return set().union(
            *(_parse_dates(match.group()) for match in DATE_PATTERN.finditer(value))
        )
    return set()


def _is_legal_advice_request(message: str) -> bool:
    return any(pattern.search(message) for pattern in LEGAL_ADVICE_PATTERNS)


def _guardrail_answer(answer: str, tool_results: list[Any], lang: str) -> str:
    supported_dates = _dates_in(tool_results)
    for match in DATE_PATTERN.finditer(answer):
        if not (_parse_dates(match.group()) & supported_dates):
            return UNVERIFIED_DATE_RESPONSE[lang]

    class_labels = {
        "A": "Non-hazardous" if lang == "en" else "No peligrosa",
        "B": "Hazardous" if lang == "en" else "Peligrosa",
        "C": "Immediately hazardous" if lang == "en" else "Inmediatamente peligrosa",
    }
    for match in re.finditer(r"\b(?:class|clase)\s+([ABC])\b", answer, re.IGNORECASE):
        following_text = answer[match.end() : match.end() + 80]
        if class_labels[match.group(1).upper()] not in following_text:
            return UNVERIFIED_CLASS_RESPONSE[lang]
    return answer


class Agent:
    def __init__(self, lang: str = "en") -> None:
        self.lang = lang
        self.settings = get_settings()

    async def _generate(
        self, client: httpx.AsyncClient, contents: list[dict[str, Any]]
    ) -> dict[str, Any]:
        model = self.settings.llm_model
        if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
            raise RuntimeError("LLM_MODEL is not a valid Gemini model name.")

        response = await client.post(
            f"{API_URL}/{model}:generateContent",
            headers={"x-goog-api-key": self.settings.llm_api_key},
            json={
                "systemInstruction": {"parts": [{"text": system_prompt(self.lang)}]},
                "contents": contents,
                "tools": [{"functionDeclarations": tools.TOOL_DEFINITIONS}],
            },
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Gemini returned an invalid response payload.")
        return payload

    async def run(self, message: str, bin_: str | None = None) -> str:
        if _is_legal_advice_request(message):
            return LEGAL_ADVICE_REFUSAL[self.lang]
        if not self.settings.llm_api_key:
            raise RuntimeError("LLM_API_KEY is not set")
        if not self.settings.llm_model:
            raise RuntimeError("LLM_MODEL is not set")

        user_message = message
        if bin_:
            user_message = f"{message}\n\nThe current building's BIN is {bin_}."
        contents: list[dict[str, Any]] = [
            {"role": "user", "parts": [{"text": user_message}]}
        ]
        tool_results: list[Any] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for step in range(1, MAX_STEPS + 1):
                payload = await self._generate(client, contents)
                candidates = payload.get("candidates")
                if (
                    not isinstance(candidates, list)
                    or not candidates
                    or not isinstance(candidates[0], dict)
                ):
                    raise RuntimeError("Gemini returned no candidate response.")

                candidate_content = candidates[0].get("content", {})
                if not isinstance(candidate_content, dict):
                    raise RuntimeError("Gemini returned an invalid candidate response.")
                parts = candidate_content.get("parts", [])
                if not isinstance(parts, list):
                    raise RuntimeError("Gemini returned invalid candidate parts.")

                function_calls = [
                    part["functionCall"]
                    for part in parts
                    if isinstance(part, dict)
                    and isinstance(part.get("functionCall"), dict)
                ]
                if not function_calls:
                    answer = "\n".join(
                        part["text"]
                        for part in parts
                        if isinstance(part, dict)
                        and isinstance(part.get("text"), str)
                    ).strip()
                    if not answer:
                        raise RuntimeError("Gemini returned no answer text.")
                    return _guardrail_answer(answer, tool_results, self.lang)

                contents.append(candidate_content)
                function_responses = []
                for function_call in function_calls:
                    name = function_call.get("name")
                    arguments = function_call.get("args", {})
                    if not isinstance(name, str) or not isinstance(arguments, dict):
                        raise RuntimeError("Gemini returned an invalid function call.")
                    arguments = deepcopy(arguments)

                    tool = TOOL_REGISTRY.get(name)
                    if tool is None:
                        log.warning(
                            "Gemini requested an unknown agent tool",
                            extra={
                                "event": "agent_tool_unknown",
                                "tool_name": name,
                                "step": step,
                            },
                        )
                        result: Any = {"error": "Unknown tool."}
                    else:
                        if bin_ and name in {
                            "lookup_violations",
                            "check_deadlines",
                            "draft_letter",
                        }:
                            arguments["bin"] = bin_
                        log.info(
                            "Agent tool call started",
                            extra={
                                "event": "agent_tool_started",
                                "tool_name": name,
                                "step": step,
                            },
                        )
                        completed = False
                        try:
                            result = await tool(**arguments)
                            tool_results.append(result)
                            completed = True
                        finally:
                            log.info(
                                "Agent tool call completed"
                                if completed
                                else "Agent tool call failed",
                                extra={
                                    "event": (
                                        "agent_tool_completed"
                                        if completed
                                        else "agent_tool_failed"
                                    ),
                                    "tool_name": name,
                                    "step": step,
                                },
                            )

                    function_responses.append(
                        {
                            "functionResponse": {
                                "name": name,
                                "response": {"result": result},
                            }
                        }
                    )

                if step == MAX_STEPS:
                    raise RuntimeError(
                        f"Agent exceeded the maximum of {MAX_STEPS} tool steps."
                    )
                contents.append({"role": "user", "parts": function_responses})

        raise RuntimeError("Agent stopped without producing an answer.")
