"""AI assistant endpoints."""

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent import tools
from app.agent.agent import Agent
from app.data import hpd_client
from app.i18n import normalize

router = APIRouter(prefix="/agent")


class DraftRequest(BaseModel):
    bin: str = Field(pattern=r"^\d{7}$")
    address: str = Field(max_length=200)
    apartment: str = Field(default="", max_length=20)
    tenant_name: str = Field(default="", max_length=100)
    lang: str = "en"


class AskRequest(BaseModel):
    message: str = Field(max_length=2000)
    bin: str | None = Field(default=None, pattern=r"^\d{7}$")
    lang: str = "en"


@router.post("/draft")
async def draft(req: DraftRequest) -> dict[str, str]:
    violations = await hpd_client.get_open_violations(req.bin)
    letter = tools.draft_letter(
        address=req.address,
        violations=violations,
        lang=normalize(req.lang),
        apartment=req.apartment,
        tenant_name=req.tenant_name,
    )
    return {"letter": letter}


@router.post("/ask")
async def ask(req: AskRequest) -> dict[str, str]:
    try:
        answer = await Agent(lang=normalize(req.lang)).run(req.message, req.bin)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Gemini request timed out") from exc
    except (RuntimeError, NotImplementedError) as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    return {"answer": answer}
