"""Make a minimal OpenAI Responses API request to verify local configuration."""

from typing import Any

import httpx

from app.config import Settings, get_settings

API_URL = "https://api.openai.com/v1/responses"
TEST_PROMPT = "Reply with exactly: TenantTrack LLM connection works."


def extract_output_text(payload: dict[str, Any]) -> str:
    """Collect assistant text from a Responses API payload."""
    parts = []
    for item in payload.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if (
                isinstance(content, dict)
                and content.get("type") == "output_text"
                and isinstance(content.get("text"), str)
            ):
                parts.append(content["text"])
    return "\n".join(parts).strip()


def run_smoke_test(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    if not settings.llm_api_key:
        raise RuntimeError("Set LLM_API_KEY in .env before running the OpenAI smoke test.")
    if not settings.llm_model:
        raise RuntimeError("Set LLM_MODEL in .env before running the OpenAI smoke test.")

    with httpx.Client(timeout=30) as client:
        response = client.post(
            API_URL,
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json={
                "model": settings.llm_model,
                "input": TEST_PROMPT,
                "max_output_tokens": 64,
            },
        )
        response.raise_for_status()

    text = extract_output_text(response.json())
    if not text:
        raise RuntimeError("OpenAI returned no text for the smoke test prompt.")
    return text


def main() -> None:
    settings = get_settings()
    if not settings.llm_api_key:
        raise SystemExit("Set LLM_API_KEY in .env before running the OpenAI smoke test.")
    if not settings.llm_model:
        raise SystemExit("Set LLM_MODEL in .env before running the OpenAI smoke test.")
    text = run_smoke_test(settings)
    print(f"OpenAI Responses API request succeeded with model {settings.llm_model}.")
    print(f"Model response: {text}")


if __name__ == "__main__":
    main()
