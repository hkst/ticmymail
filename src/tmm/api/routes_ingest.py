from fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter()


class IngestPayload(BaseModel):
    schema_version: str = Field(..., example="v1")
    event_type: str = Field(..., example="new")
    message_id: str
    thread_id: str
    subject: str
    body: str
    sender: str


@router.post("/incidents/ingest", tags=["ingest"], status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def ingest(payload: IngestPayload):
    return {"detail": "Not implemented", "idempotent": True}
