from fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter()


class EmailPayload(BaseModel):
    to: str
    subject: str
    template_key: str | None = None
    body: str | None = None
    message_id: str
    thread_id: str


@router.post("/comm/email", tags=["email"], status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def send_email(payload: EmailPayload):
    return {"detail": "Not implemented", "sent": False}
