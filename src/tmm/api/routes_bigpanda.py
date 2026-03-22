from fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter()


class BigPandaPayload(BaseModel):
    host: str
    service: str
    status: str
    description: str


@router.post("/integrations/bigpanda/events", tags=["bigpanda"], status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def bigpanda_events(payload: list[BigPandaPayload]):
    return {"detail": "Not implemented", "ok": False}
