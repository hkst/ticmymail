from time import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Header, HTTPException
from pydantic import BaseModel, Field, ValidationError
from tmm.config.loader import ConfigLoader
from tmm.logger import log_event
from tmm.service.dedupe_engine import DedupeEngine, ADLSDedupeEngine
from tmm.service.incident_service import IncidentService

router = APIRouter()


def _create_service():
    loader = ConfigLoader()
    app_cfg = loader.app()
    dedupe_backend = app_cfg.get("dedupe", {}).get("backend", "memory")
    if dedupe_backend == "adls":
        dedupe_engine = ADLSDedupeEngine(app_cfg)
    else:
        dedupe_engine = DedupeEngine()

    return IncidentService(dedupe_engine)


service = _create_service()


class IngestPayload(BaseModel):
    schema_version: str = Field(..., example="v1")
    event_type: str = Field(..., example="new")
    message_id: str
    thread_id: str
    subject: str
    body: str
    sender: str


def _unwrap_outlook_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    value = payload.get("value")
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return first

    return payload


def _get_sender(event: Dict[str, Any]) -> Optional[str]:
    if event.get("sender"):
        return event.get("sender")

    from_section = event.get("from")
    if isinstance(from_section, dict):
        email_address = from_section.get("emailAddress")
        if isinstance(email_address, dict):
            return email_address.get("address")

    return None


def _map_priority_hint(importance: Optional[str]) -> Optional[str]:
    if not importance:
        return None

    normalized = str(importance).lower()
    if normalized in {"low", "normal", "high"}:
        return normalized
    return importance


def _build_ingest_payload(raw_payload: Dict[str, Any]) -> Dict[str, Any]:
    event = _unwrap_outlook_event(raw_payload)

    normalized_payload: Dict[str, Any] = {
        "schema_version": raw_payload.get("schema_version") or event.get("schema_version"),
        "event_type": event.get("event_type"),
        "message_id": event.get("id") or event.get("message_id"),
        "thread_id": event.get("conversationId") or event.get("thread_id"),
        "subject": event.get("subject"),
        "body": event.get("bodyPreview") or event.get("body"),
        "sender": _get_sender(event),
    }

    priority_hint = _map_priority_hint(event.get("importance"))
    if priority_hint:
        normalized_payload["priority_hint"] = priority_hint

    if event.get("receivedDateTime"):
        normalized_payload.setdefault("ingested_at", event.get("receivedDateTime"))
    elif event.get("createdDateTime"):
        normalized_payload.setdefault("ingested_at", event.get("createdDateTime"))

    if event.get("reported_at"):
        normalized_payload["reported_at"] = event.get("reported_at")

    if event.get("attachments") is not None:
        normalized_payload["attachments"] = event.get("attachments")

    if event.get("correlation_hints") is not None:
        normalized_payload["correlation_hints"] = event.get("correlation_hints")

    return {**event, **normalized_payload}


@router.post("/incidents/ingest", tags=["ingest"])
async def ingest(
    body: Dict[str, Any] = Body(...),
    idem_key: str = Header(..., alias="Idempotency-Key"),
    correlation_id: Optional[str] = Header(None, alias="X-Correlation-Id"),
):
    try:
        normalized_payload = _build_ingest_payload(body)
        ingest_payload = IngestPayload(**normalized_payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())

    loader = ConfigLoader()
    app_cfg = loader.app()
    if app_cfg.get("hot_reload", {}).get("enabled", False):
        loader.enable_hot_reload(True)
        loader.reload()

    start = time()
    result = service.ingest(normalized_payload, idem_key)
    duration_ms = (time() - start) * 1000

    log_event(
        route="/v1/incidents/ingest",
        outcome=result.get("status", "unknown"),
        duration_ms=duration_ms,
        corr_id=correlation_id,
        idem_key=idem_key,
        schema_version=ingest_payload.schema_version,
        rules_version=app_cfg.get("config_version", "v1"),
        sn_sys_id=result.get("sn_sys_id"),
    )

    return result
