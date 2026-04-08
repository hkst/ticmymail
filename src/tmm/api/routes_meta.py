from time import time

from fastapi import APIRouter
from tmm.config.loader import ConfigLoader
from tmm.logger import get_run_log_path, log_event

router = APIRouter()


@router.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


@router.get("/version", tags=["meta"])
async def version():
    loader = ConfigLoader()
    app_cfg = loader.app()
    start = time()
    schema_cfg = loader.schema(app_cfg.get("config_version", "v1"))
    dedupe_cfg = loader.dedupe(app_cfg.get("config_version", "v1"))
    nfr_cfg = loader.nfr()
    duration_ms = (time() - start) * 1000
    result = {
        "service_version": "0.1.0",
        "app_config_version": app_cfg.get("config_version", "v1"),
        "schema_version": app_cfg.get("config_version", "v1"),
        "dedupe_rules_version": app_cfg.get("config_version", "v1"),
        "incident_backend": app_cfg.get("incident_backend", "servicenow"),
        "schema_config_title": schema_cfg.get("title"),
        "dedupe_rules": dedupe_cfg.get("dedupe_fields"),
        "nfr": nfr_cfg,
        "log_file": get_run_log_path(),
    }
    log_event(
        route="/v1/version",
        outcome="ok",
        duration_ms=duration_ms,
        schema_version=app_cfg.get("config_version", "v1"),
        rules_version=app_cfg.get("config_version", "v1"),
    )
    return result
