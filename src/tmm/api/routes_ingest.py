from datetime import datetime
from typing import Any, Dict, List, Optional
import time

from fastapi import APIRouter, Body, Header, HTTPException
from pydantic import BaseModel, Field, ValidationError
from tmm.config.loader import ConfigLoader
from tmm.logger import log_event
from tmm.service.errors import AppError
from tmm.service.dedupe_engine import DedupeEngine, ADLSDedupeEngine
from tmm.service.incident_service import IncidentService

router = APIRouter()
_SERVICE_CACHE: Dict[str, IncidentService] = {}


def _create_service(loader: ConfigLoader):
    app_cfg = loader.app()
    cache_key = f"{loader.root.resolve()}::{app_cfg.get('config_version', 'v1')}::{app_cfg.get('incident_backend', 'servicenow')}"
    if app_cfg.get("hot_reload", {}).get("enabled", False):
        _SERVICE_CACHE.pop(cache_key, None)

    if cache_key in _SERVICE_CACHE:
        return _SERVICE_CACHE[cache_key]

    dedupe_rules = loader.dedupe(app_cfg.get("config_version", "v1"))
    dedupe_backend = app_cfg.get("dedupe", {}).get("backend", "memory")
    if dedupe_backend == "adls":
        dedupe_engine = ADLSDedupeEngine(app_cfg)
    else:
        dedupe_engine = DedupeEngine(dedupe_rules)

    service = IncidentService(dedupe_engine, loader=loader)
    _SERVICE_CACHE[cache_key] = service
    return service


class IngestPayload(BaseModel):
    schema_version: str = Field(..., example="v1")
    event_type: str = Field(..., example="new")
    message_id: str
    thread_id: str
    reported_at: Optional[str] = None
    ingested_at: Optional[str] = None
    subject: str
    body: str
    sender: str
    attachments: Optional[List[Dict[str, Any]]] = None
    priority_hint: Optional[str] = None
    correlation_hints: Optional[List[str]] = None
    target_system: Optional[str] = None


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
    loader = ConfigLoader()
    try:
        normalized_payload = _build_ingest_payload(body)
        loader.schema(normalized_payload.get("schema_version", "v1"))
        loader.dedupe(normalized_payload.get("schema_version", "v1"))
        ingest_payload = IngestPayload(**normalized_payload)
    except FileNotFoundError as exc:
        raise AppError("RULESET_MISSING", str(exc), status_code=500)
    except ValidationError as exc:
        raise AppError("INVALID_SCHEMA", "Payload validation failed", status_code=422, details=exc.errors())

    app_cfg = loader.app()
    if app_cfg.get("hot_reload", {}).get("enabled", False):
        loader.enable_hot_reload(True)
        loader.reload()

    service = _create_service(loader)
    start = time.time()
    result = service.ingest(normalized_payload, idem_key)
    duration_ms = (time.time() - start) * 1000

    log_event(
        route="/v1/incidents/ingest",
        outcome=result.get("status", "unknown"),
        duration_ms=duration_ms,
        corr_id=correlation_id,
        idem_key=idem_key,
        schema_version=ingest_payload.schema_version,
        rules_version=app_cfg.get("config_version", "v1"),
        sn_sys_id=result.get("sn_sys_id"),
        extra={
            "ticket_system": result.get("ticket_system"),
            "ticket_id": result.get("ticket_id"),
            "jira_issue_key": result.get("jira_issue_key"),
            "action": result.get("action"),
        },
    )

    return result
