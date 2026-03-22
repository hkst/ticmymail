from time import time

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from tmm.config.loader import ConfigLoader
from tmm.logger import log_event
from tmm.service.dedupe_engine import DedupeEngine
from tmm.service.incident_service import IncidentService

router = APIRouter()
service = IncidentService(DedupeEngine())


class IngestPayload(BaseModel):
    schema_version: str = Field(..., example="v1")
    event_type: str = Field(..., example="new")
    message_id: str
    thread_id: str
    subject: str
    body: str
    sender: str


@router.post("/incidents/ingest", tags=["ingest"])
async def ingest(request: Request, payload: IngestPayload):
    loader = ConfigLoader()
    app_cfg = loader.app()
    if app_cfg.get("hot_reload", {}).get("enabled", False):
        loader.enable_hot_reload(True)
        loader.reload()

    idem_key = request.headers.get("Idempotency-Key")
    if not idem_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header required")

    start = time()
    result = service.ingest(payload.model_dump(), idem_key)
    duration_ms = (time() - start) * 1000

    log_event(
        route="/v1/incidents/ingest",
        outcome=result.get("status", "unknown"),
        duration_ms=duration_ms,
        corr_id=request.headers.get("X-Correlation-Id"),
        idem_key=idem_key,
        schema_version=payload.schema_version,
        rules_version=app_cfg.get("config_version", "v1"),
        sn_sys_id=result.get("sn_sys_id"),
    )

    return result
