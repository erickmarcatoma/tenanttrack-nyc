"""Gemini-backed agent that can call TenantTrack data tools."""

import logging
import re
from copy import deepcopy
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


def system_prompt(lang: str = "en") -> str:
    name = "es.md" if lang == "es" else "en.md"
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


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
                    return answer

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
