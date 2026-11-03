"""One agent with a tool loop.

Flow: the user message + tool definitions go to the LLM; when it asks for a tool,
we run it from tools.py and send the result back; repeat until it answers.
The LLM provider is chosen in Phase 4 (see PLAN.md).
"""

from pathlib import Path

from app.agent import tools
from app.config import get_settings

PROMPTS_DIR = Path(__file__).parent / "prompts"
MAX_STEPS = 6

TOOL_REGISTRY = {
    "lookup_violations": tools.lookup_violations,
    "check_deadlines": tools.check_deadlines,
    "draft_letter": tools.draft_letter,
}


def system_prompt(lang: str = "en") -> str:
    name = "es.md" if lang == "es" else "en.md"
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


class Agent:
    def __init__(self, lang: str = "en") -> None:
        self.lang = lang
        self.settings = get_settings()

    async def run(self, message: str, bin_: str | None = None) -> str:
        if not self.settings.llm_api_key:
            raise RuntimeError("LLM_API_KEY is not set")
        # TODO (Phase 4): call the LLM with system_prompt(self.lang), the message,
        # and TOOL_REGISTRY as tools; loop up to MAX_STEPS.
        raise NotImplementedError("Agent loop is planned for Phase 4")
