import asyncio
import logging

import httpx
import pytest

from app.agent import agent as agent_module
from app.config import Settings


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def candidate(*parts):
    return {"candidates": [{"content": {"role": "model", "parts": list(parts)}}]}


def configure_agent(monkeypatch, responses, model="gemini-test"):
    settings = Settings(_env_file=None, llm_api_key="test-key", llm_model=model)
    monkeypatch.setattr(agent_module, "get_settings", lambda: settings)
    requests = []

    class AsyncClient:
        def __init__(self, *, timeout):
            assert timeout == 30

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, *, headers, json):
            requests.append({"url": url, "headers": headers, "json": json})
            return FakeResponse(responses.pop(0))

    monkeypatch.setattr(agent_module.httpx, "AsyncClient", AsyncClient)
    return requests


def test_agent_returns_text_response(monkeypatch):
    requests = configure_agent(monkeypatch, [candidate({"text": "Hello, tenant."})])

    answer = asyncio.run(agent_module.Agent(lang="es").run("Hola"))

    assert answer == "Hello, tenant."
    request = requests[0]
    assert request["url"].endswith("/gemini-test:generateContent")
    assert request["headers"] == {"x-goog-api-key": "test-key"}
    assert request["json"]["contents"] == [
        {"role": "user", "parts": [{"text": "Hola"}]}
    ]
    assert request["json"]["systemInstruction"]["parts"][0]["text"] == (
        agent_module.system_prompt("es")
    )
    assert request["json"]["tools"] == [
        {"functionDeclarations": agent_module.tools.TOOL_DEFINITIONS}
    ]


def test_agent_propagates_gemini_timeout(monkeypatch):
    settings = Settings(
        _env_file=None,
        llm_api_key="test-key",
        llm_model="gemini-test",
    )
    monkeypatch.setattr(agent_module, "get_settings", lambda: settings)

    class AsyncClient:
        def __init__(self, *, timeout):
            assert timeout == 30

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, *, headers, json):
            raise httpx.ReadTimeout("Gemini request timed out")

    monkeypatch.setattr(agent_module.httpx, "AsyncClient", AsyncClient)

    with pytest.raises(httpx.ReadTimeout, match="Gemini request timed out"):
        asyncio.run(agent_module.Agent().run("Hello"))


@pytest.mark.parametrize(
    ("answer", "tool_results", "expected"),
    [
        (
            "The deadline is Jan 11, 2026.",
            [{"deadline": "2026-01-11"}],
            "The deadline is Jan 11, 2026.",
        ),
        (
            "The deadline is Jan 12, 2026.",
            [{"deadline": "2026-01-11"}],
            agent_module.UNVERIFIED_DATE_RESPONSE["en"],
        ),
        (
            "The deadline is 11 de ene. de 2026.",
            [{"deadline": "2026-01-11"}],
            "The deadline is 11 de ene. de 2026.",
        ),
        (
            "The deadline is 1/11/2026.",
            [{"deadline": "2026-01-11"}],
            "The deadline is 1/11/2026.",
        ),
        (
            "The deadline is 1/12/2026.",
            [{"deadline": "2026-01-11"}],
            agent_module.UNVERIFIED_DATE_RESPONSE["en"],
        ),
        (
            "The deadline is January 11th, 2026.",
            [{"deadline": "2026-01-11"}],
            "The deadline is January 11th, 2026.",
        ),
        (
            "The deadline is 1/12/26.",
            [{"deadline": "2026-01-11"}],
            agent_module.UNVERIFIED_DATE_RESPONSE["en"],
        ),
    ],
)
def test_guardrail_only_allows_dates_from_tool_results(answer, tool_results, expected):
    assert agent_module._guardrail_answer(answer, tool_results, "en") == expected


def test_agent_replaces_model_date_not_returned_by_tool(monkeypatch):
    configure_agent(
        monkeypatch,
        [
            candidate(
                {
                    "functionCall": {
                        "name": "check_deadlines",
                        "args": {"bin": "1111111"},
                    }
                }
            ),
            candidate({"text": "The deadline is Jan 12, 2026."}),
        ],
    )

    async def check_deadlines(**kwargs):
        return [{"id": "123", "deadline": "2026-01-11", "status": "overdue"}]

    monkeypatch.setitem(agent_module.TOOL_REGISTRY, "check_deadlines", check_deadlines)

    answer = asyncio.run(agent_module.Agent().run("When is the deadline?"))

    assert answer == agent_module.UNVERIFIED_DATE_RESPONSE["en"]


@pytest.mark.parametrize(
    ("answer", "lang", "expected"),
    [
        (
            "Class C is serious.",
            "en",
            agent_module.UNVERIFIED_CLASS_RESPONSE["en"],
        ),
        (
            "La Clase C es grave.",
            "es",
            agent_module.UNVERIFIED_CLASS_RESPONSE["es"],
        ),
        ("Class C is Immediately hazardous.", "en", "Class C is Immediately hazardous."),
        (
            "La Clase C es Inmediatamente peligrosa.",
            "es",
            "La Clase C es Inmediatamente peligrosa.",
        ),
    ],
)
def test_guardrail_requires_official_class_label(answer, lang, expected):
    assert agent_module._guardrail_answer(answer, [], lang) == expected


@pytest.mark.parametrize(
    ("message", "lang", "expected"),
    [
        (
            "Should I sue my landlord?",
            "en",
            agent_module.LEGAL_ADVICE_REFUSAL["en"],
        ),
        (
            "¿Debo demandar al propietario?",
            "es",
            agent_module.LEGAL_ADVICE_REFUSAL["es"],
        ),
    ],
)
def test_agent_refuses_legal_advice_without_calling_model(
    monkeypatch, message, lang, expected
):
    requests = configure_agent(monkeypatch, [])

    answer = asyncio.run(agent_module.Agent(lang=lang).run(message))

    assert answer == expected
    assert requests == []


def test_agent_executes_tool_and_sends_result_back(monkeypatch):
    responses = [
        candidate(
            {
                "functionCall": {
                    "name": "lookup_violations",
                    "args": {"bin": "1111111"},
                },
                "thoughtSignature": "preserve-this",
            }
        ),
        candidate({"text": "There is one open violation."}),
    ]
    requests = configure_agent(monkeypatch, responses)
    calls = []

    async def lookup_violations(**kwargs):
        calls.append(kwargs)
        return [{"id": "123", "class": "C"}]

    monkeypatch.setitem(
        agent_module.TOOL_REGISTRY, "lookup_violations", lookup_violations
    )

    records = []
    handler = logging.Handler()
    handler.emit = records.append
    agent_module.log.addHandler(handler)
    try:
        answer = asyncio.run(
            agent_module.Agent().run("Show violations", bin_="2222222")
        )
    finally:
        agent_module.log.removeHandler(handler)

    assert answer == "There is one open violation."
    assert calls == [{"bin": "2222222"}]
    followup_contents = requests[1]["json"]["contents"]
    assert followup_contents[1] == {
        "role": "model",
        "parts": [
            {
                "functionCall": {
                    "name": "lookup_violations",
                    "args": {"bin": "1111111"},
                },
                "thoughtSignature": "preserve-this",
            }
        ],
    }
    assert followup_contents[2] == {
        "role": "user",
        "parts": [
            {
                "functionResponse": {
                    "name": "lookup_violations",
                    "response": {"result": [{"id": "123", "class": "C"}]},
                }
            }
        ],
    }
    tool_logs = [record for record in records if hasattr(record, "tool_name")]
    assert [record.event for record in tool_logs] == [
        "agent_tool_started",
        "agent_tool_completed",
    ]
    assert all(record.tool_name == "lookup_violations" for record in tool_logs)
    assert all("2222222" not in record.getMessage() for record in records)


def test_agent_stops_at_maximum_tool_steps(monkeypatch):
    responses = [
        candidate({"functionCall": {"name": "lookup_violations", "args": {"bin": "1111111"}}})
        for _ in range(agent_module.MAX_STEPS)
    ]
    requests = configure_agent(monkeypatch, responses)

    async def lookup_violations(**kwargs):
        return []

    monkeypatch.setitem(
        agent_module.TOOL_REGISTRY, "lookup_violations", lookup_violations
    )

    with pytest.raises(RuntimeError, match="maximum of 6 tool steps"):
        asyncio.run(agent_module.Agent().run("Continue"))

    assert len(requests) == agent_module.MAX_STEPS


def test_agent_logs_failed_tool_without_swallowing_error(monkeypatch):
    requests = configure_agent(
        monkeypatch,
        [
            candidate(
                {
                    "functionCall": {
                        "name": "lookup_violations",
                        "args": {"bin": "1111111"},
                    }
                }
            )
        ],
    )

    async def lookup_violations(**kwargs):
        raise ValueError("tool failed")

    monkeypatch.setitem(
        agent_module.TOOL_REGISTRY, "lookup_violations", lookup_violations
    )

    records = []
    handler = logging.Handler()
    handler.emit = records.append
    agent_module.log.addHandler(handler)
    try:
        with pytest.raises(ValueError, match="tool failed"):
            asyncio.run(agent_module.Agent().run("Show violations"))
    finally:
        agent_module.log.removeHandler(handler)

    assert [record.event for record in records if hasattr(record, "event")] == [
        "agent_tool_started",
        "agent_tool_failed",
    ]
    assert len(requests) == 1


@pytest.mark.parametrize(
    ("api_key", "model", "message"),
    [
        ("", "gemini-test", "LLM_API_KEY"),
        ("test-key", "", "LLM_MODEL"),
    ],
)
def test_agent_requires_configuration(monkeypatch, api_key, model, message):
    settings = Settings(_env_file=None, llm_api_key=api_key, llm_model=model)
    monkeypatch.setattr(agent_module, "get_settings", lambda: settings)

    with pytest.raises(RuntimeError, match=message):
        asyncio.run(agent_module.Agent().run("Hello"))
