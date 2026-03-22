from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from tmm.adapters.servicenow_client import ServiceNowClient
from tmm.config.loader import ConfigLoader
from tmm.logger import log_event

router = APIRouter()


class ServiceNowPayload(BaseModel):
    subject: str
    body: str
    sender: str
    sys_id: str | None = None


@router.post("/integrations/servicenow/incidents", tags=["servicenow"])
async def create_incident(request: Request, payload: ServiceNowPayload):
    loader = ConfigLoader()
    app_cfg = loader.app()
    if app_cfg.get("hot_reload", {}).get("enabled", False):
        loader.enable_hot_reload(True)
        loader.reload()

    sn_cfg = loader.servicenow()
    client = ServiceNowClient(sn_cfg)

    try:
        response = client.create_incident(payload.model_dump())
        outcome = "created"
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    log_event(
        route="/v1/integrations/servicenow/incidents",
        outcome=outcome,
        duration_ms=0,
        corr_id=request.headers.get("X-Correlation-Id"),
        idem_key=request.headers.get("Idempotency-Key"),
        schema_version="v1",
        rules_version=app_cfg.get("config_version", "v1"),
        sn_sys_id=response.get("payload", {}).get("caller_id"),
    )

    return response


@router.post("/integrations/servicenow/incidents/{sys_id}/comment", tags=["servicenow"])
async def comment_incident(sys_id: str, payload: dict, request: Request):
    loader = ConfigLoader()
    app_cfg = loader.app()
    if app_cfg.get("hot_reload", {}).get("enabled", False):
        loader.enable_hot_reload(True)
        loader.reload()

    sn_cfg = loader.servicenow()
    client = ServiceNowClient(sn_cfg)

    comment = payload.get("comment")
    if not comment:
        raise HTTPException(status_code=400, detail="comment is required")

    result = client.add_comment(sys_id, comment)

    log_event(
        route=f"/v1/integrations/servicenow/incidents/{sys_id}/comment",
        outcome="commented",
        duration_ms=0,
        corr_id=request.headers.get("X-Correlation-Id") if request else None,
        idem_key=request.headers.get("Idempotency-Key") if request else None,
        schema_version="v1",
        rules_version=app_cfg.get("config_version", "v1"),
        sn_sys_id=sys_id,
    )

    return result
