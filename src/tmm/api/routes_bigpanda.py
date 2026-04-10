from time import time

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
from tmm.adapters.bigpanda_client import BigPandaClient
from tmm.config.loader import ConfigLoader
from tmm.logger import log_event
from tmm.service.errors import AppError

router = APIRouter()


class BigPandaPayload(BaseModel):
    host: str
    service: str
    status: str
    description: str
    tags: list[str] | None = None


@router.post("/integrations/bigpanda/events", tags=["bigpanda"])
async def bigpanda_events(request: Request, payload: list[BigPandaPayload]):
    loader = ConfigLoader()
    app_cfg = loader.app()
    if app_cfg.get("hot_reload", {}).get("enabled", False):
        loader.enable_hot_reload(True)
        loader.reload()

    bp_cfg = loader.bigpanda()
    client = BigPandaClient(bp_cfg)

    results = []
    start = time()
    for event in payload:
        try:
            result = client.post_alert(event.model_dump())
            results.append(result)
        except Exception as exc:
            raise AppError("BIGPANDA_4XX", str(exc), status_code=400)

    duration_ms = (time() - start) * 1000

    log_event(
        route="/v1/integrations/bigpanda/events",
        outcome="posted",
        duration_ms=duration_ms,
        corr_id=request.headers.get("X-Correlation-Id"),
        idem_key=request.headers.get("Idempotency-Key"),
        schema_version="v1",
        rules_version=app_cfg.get("config_version", "v1"),
    )
    return {"ok": True, "ref": results[0].get("operation") if results else None, "results": results}


class BigPandaQuery(BaseModel):
    tags: list[str]
    service: str
    window_minutes: int | None = None


@router.post("/integrations/bigpanda/search", tags=["bigpanda"])
async def bigpanda_search(request: Request, query: BigPandaQuery):
    loader = ConfigLoader()
    bp_cfg = loader.bigpanda()
    client = BigPandaClient(bp_cfg)

    start = time()
    similar = client.find_similar_alerts(query.tags, query.service, query.window_minutes)
    duration_ms = (time() - start) * 1000

    log_event(
        route="/v1/integrations/bigpanda/search",
        outcome="found",
        duration_ms=duration_ms,
        corr_id=request.headers.get("X-Correlation-Id"),
        idem_key=request.headers.get("Idempotency-Key"),
        schema_version="v1",
        rules_version=loader.app().get("config_version", "v1"),
    )
    return {"ok": True, "similar": similar}


class BigPandaCorrelation(BaseModel):
    alert_id: str
    correlation_ids: list[str]


@router.post("/integrations/bigpanda/correlate", tags=["bigpanda"])
async def bigpanda_correlate(request: Request, payload: BigPandaCorrelation):
    loader = ConfigLoader()
    bp_cfg = loader.bigpanda()
    client = BigPandaClient(bp_cfg)

    try:
        start = time()
        response = client.attach_correlation_ids(payload.alert_id, payload.correlation_ids)
    except Exception as exc:
        raise AppError("BIGPANDA_4XX", str(exc), status_code=400)

    duration_ms = (time() - start) * 1000

    log_event(
        route="/v1/integrations/bigpanda/correlate",
        outcome="correlated",
        duration_ms=duration_ms,
        corr_id=request.headers.get("X-Correlation-Id"),
        idem_key=request.headers.get("Idempotency-Key"),
        schema_version="v1",
        rules_version=loader.app().get("config_version", "v1"),
    )
    return response
