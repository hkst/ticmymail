from time import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from tmm.config.loader import ConfigLoader
from tmm.logger import log_event

router = APIRouter()


class EmailPayload(BaseModel):
    to: str
    subject: str
    template_key: str | None = None
    body: str | None = None
    message_id: str
    thread_id: str


@router.post("/comm/email", tags=["email"])
async def send_email(request: Request, payload: EmailPayload):
    loader = ConfigLoader()
    app_cfg = loader.app()
    if app_cfg.get("hot_reload", {}).get("enabled", False):
        loader.enable_hot_reload(True)
        loader.reload()

    if not payload.message_id or not payload.thread_id:
        raise HTTPException(status_code=400, detail="message_id and thread_id are required")

    start = time()
    of = {
        "sent": True,
        "provider": "mock",
        "in_reply_to": payload.message_id,
        "references": payload.thread_id,
    }
    duration_ms = (time() - start) * 1000

    log_event(
        route="/v1/comm/email",
        outcome="sent",
        duration_ms=duration_ms,
        corr_id=request.headers.get("X-Correlation-Id"),
        idem_key=request.headers.get("Idempotency-Key"),
        schema_version=payload.template_key or "v1",
        rules_version=app_cfg.get("config_version", "v1"),
    )

    return of
