import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


class BigPandaClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.api_url = self.config.get("api_url", "")
        self.api_token = self.config.get("api_token", "")
        self.time_window_minutes = int(self.config.get("time_window_minutes", 60))
        self.retry_policy = self.config.get("retry_policy", {"max_attempts": 1, "backoff_seconds": 0})
        self.enable_correlation = bool(self.config.get("enable_correlation", False))

    @staticmethod
    def _sleep(seconds: float) -> None:
        time.sleep(seconds)

    def _execute_api_call(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        max_attempts = int(self.retry_policy.get("max_attempts", 1))
        backoff = float(self.retry_policy.get("backoff_seconds", 0))
        last_exc = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = {
                    "operation": operation,
                    "api_url": self.api_url,
                    "payload": payload,
                    "access_token": self.api_token,
                    "attempt": attempt,
                    "status": "ok",
                }
                return response
            except Exception as exc:
                last_exc = exc
                if attempt < max_attempts and backoff > 0:
                    self._sleep(backoff)
                continue

        raise RuntimeError(f"BigPanda {operation} failed after {max_attempts} attempts") from last_exc

    def post_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not payload.get("host") or not payload.get("service") or not payload.get("status"):
            raise ValueError("host, service, and status are mandatory for BigPanda alert")

        body = {
            "host": payload["host"],
            "service": payload["service"],
            "status": payload["status"],
            "description": payload.get("description", ""),
            "tags": payload.get("tags", []),
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        return self._execute_api_call("post_alert", body)

    def find_similar_alerts(self, tags: List[str], service: str, window_minutes: int | None = None) -> List[Dict[str, Any]]:
        if window_minutes is None:
            window_minutes = self.time_window_minutes

        window_cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        return [
            {
                "alert_id": f"sim-{idx}",
                "host": f"host{idx}",
                "service": service,
                "tags": tags,
                "at": (window_cutoff + timedelta(minutes=idx)).isoformat() + "Z",
            }
            for idx in range(0, min(3, len(tags) or 1))
        ]

    def attach_correlation_ids(self, alert_id: str, correlation_ids: List[str]) -> Dict[str, Any]:
        if not self.enable_correlation:
            raise RuntimeError("BigPanda correlation is disabled in config")
        if not alert_id or not correlation_ids:
            raise ValueError("alert_id and correlation_ids are required")

        return self._execute_api_call("attach_correlation", {"alert_id": alert_id, "correlation_ids": correlation_ids})
