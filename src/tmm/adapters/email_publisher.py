import re
import time
from typing import Any, Dict

from tmm.config.loader import ConfigLoader


class EmailPublisher:
    def __init__(self, config: Dict[str, Any], loader: ConfigLoader | None = None):
        self.config = config or {}
        self.loader = loader or ConfigLoader()
        self.provider_type = self.config.get("type", "smtp").lower()
        self.retry_policy = self.config.get("retry_policy", {"max_attempts": 1, "backoff_seconds": 0})

    @staticmethod
    def _render_template(text: str, context: Dict[str, Any]) -> str:
        def _replace(match):
            key = match.group(1)
            val = context.get(key, "")
            return str(val)

        return re.sub(r"\{\{\s*([\w_]+)\s*\}\}", _replace, text)

    def _body_from_payload(self, payload: Dict[str, Any]) -> str:
        if payload.get("template_key"):
            template_key = payload["template_key"]
            raw_template = self.loader.email_template(template_key)
            payload_vars = {k: v for k, v in payload.items() if isinstance(v, (str, int, float))}
            body = self._render_template(raw_template, payload_vars)
        else:
            body = payload.get("body", "") or ""

        wrapper = self.loader.email_wrapper()
        return self._render_template(wrapper, {"body": body})

    def _build_outgoing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = self._body_from_payload(payload)
        return {
            "to": payload.get("to"),
            "subject": payload.get("subject"),
            "body": body,
            "in_reply_to": payload.get("message_id"),
            "references": payload.get("thread_id"),
        }

    @staticmethod
    def _sleep(seconds: float) -> None:
        time.sleep(seconds)

    def _send_smtp(self, outgoing: Dict[str, Any]) -> Dict[str, Any]:
        return {"channel": "smtp_relay", "message": outgoing}

    def _send_graph(self, outgoing: Dict[str, Any]) -> Dict[str, Any]:
        return {"channel": "graph_send_only", "message": outgoing}

    def _dispatch(self, outgoing: Dict[str, Any]) -> Dict[str, Any]:
        if self.provider_type in ["smtp", "smtp_relay"]:
            return self._send_smtp(outgoing)
        if self.provider_type in ["graph", "graph_send_only"]:
            return self._send_graph(outgoing)
        raise ValueError(f"Unsupported email provider type: {self.provider_type}")

    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not payload.get("to"):
            raise ValueError("Missing destination email address")
        if not payload.get("subject"):
            raise ValueError("Missing subject")

        outgoing = self._build_outgoing(payload)

        max_attempts = int(self.retry_policy.get("max_attempts", 1))
        backoff = float(self.retry_policy.get("backoff_seconds", 0))

        last_exc = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = self._dispatch(outgoing)
                return {
                    "status": "sent",
                    "attempts": attempt,
                    "provider": response.get("channel"),
                    **response,
                }
            except Exception as exc:
                last_exc = exc
                if attempt < max_attempts and backoff > 0:
                    self._sleep(backoff)
                continue

        raise RuntimeError(f"Email send failed after {max_attempts} attempts") from last_exc
