import atexit
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

LOGGER_NAME = "tmm"
LOG_DIR = Path(os.getenv("TMM_LOG_DIR", "logs"))
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
LOG_FILE = LOG_DIR / f"run-{RUN_ID}.log"


def _configure_logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    configured_logger = logging.getLogger(LOGGER_NAME)
    configured_logger.setLevel(logging.INFO)
    configured_logger.propagate = False

    if not configured_logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        configured_logger.addHandler(handler)

    return configured_logger


logger = _configure_logger()


def get_run_log_path() -> str:
    return str(LOG_FILE)


def _log_boundary(event: str, level: str = "INFO", extra: Optional[Dict[str, Any]] = None) -> None:
    payload: Dict[str, Any] = {
        "ts": time.time(),
        "level": level,
        "event": event,
        "run_id": RUN_ID,
        "log_file": str(LOG_FILE),
    }
    if extra:
        payload.update(extra)
    logger.log(getattr(logging, level.upper(), logging.INFO), json.dumps(payload))


def log_run_start(extra: Optional[Dict[str, Any]] = None) -> None:
    _log_boundary("run_start", extra=extra)


def log_run_end(extra: Optional[Dict[str, Any]] = None) -> None:
    _log_boundary("run_end", extra=extra)


def log_error(message: str, *, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
    payload = {"message": message}
    if error_code:
        payload["error_code"] = error_code
    if details:
        payload["details"] = details
    _log_boundary("error", level="ERROR", extra=payload)


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


log_run_start()
atexit.register(log_run_end)
