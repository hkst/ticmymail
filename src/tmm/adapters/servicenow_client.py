import time
from typing import Any, Dict


class ServiceNowClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.endpoint = self.config.get("instance_url", "")
        self.mappings = self.config.get("mappings", {}).get("incident", {})
        self.retry_policy = self.config.get("retry_policy", {"max_attempts": 1, "backoff_seconds": 0})

    @staticmethod
    def _render_template(text: str, context: Dict[str, Any]) -> str:
        import re

        def _replace(match):
            key = match.group(1)
            return str(context.get(key, ""))

        return re.sub(r"\{\{\s*([\w_]+)\s*\}\}", _replace, text)

    @staticmethod
    def _sleep(seconds: float) -> None:
        time.sleep(seconds)

    def _mapped_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        mapped = {}
        for target_field, template in self.mappings.items():
            mapped[target_field] = self._render_template(template, payload)

        missing = [f for f, v in mapped.items() if not v]
        if missing:
            raise ValueError(f"Missing mandatory servicenow fields: {missing}")

        return mapped

    def create_incident(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        outgoing = self._mapped_payload(payload)
        return self._execute_api_call("create", outgoing)

    def update_incident(self, sys_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not sys_id:
            raise ValueError("ServiceNow sys_id is required for update")
        outgoing = self._mapped_payload(payload)
        outgoing["sys_id"] = sys_id
        return self._execute_api_call("update", outgoing)

    def add_comment(self, sys_id: str, comment: str) -> Dict[str, Any]:
        if not sys_id or not comment:
            raise ValueError("sys_id and comment are required")
        outgoing = {"sys_id": sys_id, "comments": comment}
        return self._execute_api_call("comment", outgoing)

    def attach_file(self, sys_id: str, file_name: str, content_base64: str) -> Dict[str, Any]:
        if not sys_id or not file_name or not content_base64:
            raise ValueError("sys_id, file_name, and content_base64 are required")
        outgoing = {"sys_id": sys_id, "file_name": file_name, "content": content_base64}
        return self._execute_api_call("attach", outgoing)

    def _execute_api_call(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        max_attempts = int(self.retry_policy.get("max_attempts", 1))
        backoff = float(self.retry_policy.get("backoff_seconds", 0))
        last_exc = None

        for attempt in range(1, max_attempts + 1):
            try:
                resp = {
                    "operation": operation,
                    "endpoint": f"{self.endpoint}/api/now/table/incident",
                    "payload": payload,
                    "attempt": attempt,
                    "status": "ok",
                }
                return resp
            except Exception as exc:
                last_exc = exc
                if attempt < max_attempts and backoff > 0:
                    self._sleep(backoff)
                continue

        raise RuntimeError(f"ServiceNow {operation} failed after {max_attempts} attempts") from last_exc
