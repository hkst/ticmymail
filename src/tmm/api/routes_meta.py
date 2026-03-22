from time import time

from fastapi import APIRouter
from tmm.config.loader import ConfigLoader
from tmm.logger import log_event

router = APIRouter()
loader = ConfigLoader()
app_cfg = loader.app()
if app_cfg.get("hot_reload", {}).get("enabled", False):
    loader.enable_hot_reload(True)


@router.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


@router.get("/version", tags=["meta"])
async def version():
    start = time()
    schema_cfg = loader.schema(app_cfg.get("config_version", "v1"))
    dedupe_cfg = loader.dedupe(app_cfg.get("config_version", "v1"))
    duration_ms = (time() - start) * 1000
    result = {
        "service_version": "0.1.0",
        "app_config_version": app_cfg.get("config_version", "v1"),
        "schema_version": app_cfg.get("config_version", "v1"),
        "dedupe_rules_version": app_cfg.get("config_version", "v1"),
        "schema_config_title": schema_cfg.get("title"),
        "dedupe_rules": dedupe_cfg.get("dedupe_fields"),
    }
    log_event(
        route="/v1/version",
        outcome="ok",
        duration_ms=duration_ms,
        schema_version=app_cfg.get("config_version", "v1"),
        rules_version=app_cfg.get("config_version", "v1"),
    )
    return result
