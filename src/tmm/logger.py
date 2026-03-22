import json
import logging
import time
from typing import Any, Dict, Optional

LOGGER_NAME = "tmm"
logger = logging.getLogger(LOGGER_NAME)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    fmt = "%(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def log_event(
    route: str,
    outcome: str,
    duration_ms: float,
    ts: Optional[float] = None,
    level: str = "INFO",
    corr_id: Optional[str] = None,
    idem_key: Optional[str] = None,
    schema_version: Optional[str] = None,
    rules_version: Optional[str] = None,
    sn_sys_id: Optional[str] = None,
    error_code: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    if ts is None:
        ts = time.time()

    payload = {
        "ts": ts,
        "level": level,
        "route": route,
        "duration_ms": duration_ms,
        "outcome": outcome,
        "corr_id": corr_id,
        "idem_key": idem_key,
        "schema_version": schema_version,
        "rules_version": rules_version,
        "sn_sys_id": sn_sys_id,
        "error_code": error_code,
    }
    if extra:
        payload.update(extra)

    logger.log(getattr(logging, level.upper(), logging.INFO), json.dumps(payload))
