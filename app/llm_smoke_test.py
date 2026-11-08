"""Make a minimal Gemini API request to verify local configuration."""

from typing import Any

import httpx

from app.config import Settings, get_settings

API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
TEST_PROMPT = "Reply with exactly: TenantTrack LLM connection works."


def extract_output_text(payload: dict[str, Any]) -> str:
    """Collect text from the first Gemini candidate."""
    parts = []
    candidates = payload.get("candidates", [])
    if candidates and isinstance(candidates[0], dict):
        content = candidates[0].get("content", {})
        if isinstance(content, dict):
            for part in content.get("parts", []):
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    parts.append(part["text"])
    return "\n".join(parts).strip()


def run_smoke_test(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    if not settings.llm_api_key:
        raise RuntimeError("Set your Gemini API key in LLM_API_KEY in .env.")
    if not settings.llm_model:
        raise RuntimeError("Set LLM_MODEL in .env before running the Gemini smoke test.")

    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{API_URL}/{settings.llm_model}:generateContent",
            headers={"x-goog-api-key": settings.llm_api_key},
            json={
                "contents": [{"parts": [{"text": TEST_PROMPT}]}],
                "generationConfig": {"maxOutputTokens": 64},
            },
        )
        response.raise_for_status()

    text = extract_output_text(response.json())
    if not text:
        raise RuntimeError("Gemini returned no text for the smoke test prompt.")
    return text


def main() -> None:
    settings = get_settings()
    if not settings.llm_api_key:
        raise SystemExit("Set your Gemini API key in LLM_API_KEY in .env.")
    if not settings.llm_model:
        raise SystemExit("Set LLM_MODEL in .env before running the Gemini smoke test.")
    text = run_smoke_test(settings)
    print(f"Gemini API request succeeded with model {settings.llm_model}.")
    print(f"Model response: {text}")


if __name__ == "__main__":
    main()
