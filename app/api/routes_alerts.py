"""Alert subscribe / unsubscribe. Planned for Phase 5."""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/alerts")


class SubscribeRequest(BaseModel):
    bin: str = Field(pattern=r"^\d{7}$")
    channel: Literal["email", "sms"]
    contact: str = Field(max_length=255)
    lang: str = "en"


@router.post("/subscribe")
def subscribe(req: SubscribeRequest):
    raise HTTPException(status_code=501, detail="Alerts are coming in v2")


@router.get("/unsubscribe/{token}")
def unsubscribe(token: str):
    # Must delete the stored contact, not just deactivate it.
    raise HTTPException(status_code=501, detail="Alerts are coming in v2")
