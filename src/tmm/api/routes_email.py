from time import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from tmm.adapters.email_publisher import EmailPublisher
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

    email_cfg = loader.email()
    publisher = EmailPublisher(email_cfg, loader=loader)

    if not payload.message_id or not payload.thread_id:
        raise HTTPException(status_code=400, detail="message_id and thread_id are required")

    start = time()
    try:
        result = publisher.send(payload.model_dump())
        outcome = "sent"
    except Exception as exc:
        result = {"status": "error", "error": str(exc)}
        outcome = "error"

    duration_ms = (time() - start) * 1000

    log_event(
        route="/v1/comm/email",
        outcome=outcome,
        duration_ms=duration_ms,
        corr_id=request.headers.get("X-Correlation-Id"),
        idem_key=request.headers.get("Idempotency-Key"),
        schema_version=payload.template_key or "v1",
        rules_version=app_cfg.get("config_version", "v1"),
        sn_sys_id=None,
    )

    return {
        "in_reply_to": payload.message_id,
        "references": payload.thread_id,
        **result,
    }
