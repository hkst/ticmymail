import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from tmm.adapters.jira_client import JiraClient
from tmm.adapters.servicenow_client import ServiceNowClient
from tmm.config.loader import ConfigLoader
from tmm.service.errors import AppError


class IncidentService:
    def __init__(self, dedupe_engine, loader: ConfigLoader | None = None):
        self.dedupe = dedupe_engine
        self.loader = loader or ConfigLoader()
        self.idempotency_store: Dict[str, Dict[str, Any]] = {}
        self.app_config = self.loader.app()
        self.default_backend = self.app_config.get("incident_backend", "servicenow")
        self._clients: Dict[str, Any] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _ticket_backend(self, payload: Dict[str, Any]) -> str:
        return str(payload.get("target_system") or self.default_backend).lower()

    def _get_client(self, backend: str):
        if backend in self._clients:
            return self._clients[backend]

        try:
            if backend == "jira":
                jira_config = self.loader.jira()
                if jira_config.get("enabled", False):
                    self._clients[backend] = JiraClient(jira_config)
                    return self._clients[backend]
                return None
            if backend == "servicenow":
                self._clients[backend] = ServiceNowClient(self.loader.servicenow())
                return self._clients[backend]
        except FileNotFoundError:
            return None

        return None

    @staticmethod
    def _build_key(payload: Dict[str, Any]) -> str:
        return f"{payload.get('message_id')}|{payload.get('thread_id')}"

    @staticmethod
    def _sender_email(payload: Dict[str, Any]) -> str | None:
        sender = payload.get("sender")
        if sender:
            return sender
        return payload.get("from", {}).get("emailAddress", {}).get("address")

    def _build_description(self, payload: Dict[str, Any]) -> str:
        lines = [payload.get("body", "")]

        sender = self._sender_email(payload)
        if sender:
            lines.append(f"\nReporter: {sender}")
        if payload.get("business"):
            lines.append(f"Business: {payload['business']}")
        if payload.get("division"):
            lines.append(f"Division: {payload['division']}")
        if payload.get("platform"):
            lines.append(f"Platform: {payload['platform']}")
        if payload.get("correlation_hints"):
            lines.append(f"Correlation hints: {', '.join(payload['correlation_hints'])}")
        if payload.get("attachments"):
            lines.append(f"Attachments: {len(payload['attachments'])}")

        return "\n".join(line for line in lines if line)

    def _create_ticket(self, payload: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        backend = self._ticket_backend(payload)
        client = self._get_client(backend)
        summary = payload.get("subject", "Incident")
        description = self._build_description(payload)

        if backend == "jira":
            if client is None:
                raise AppError("JIRA_DISABLED", "Jira integration is not enabled", status_code=503)
            try:
                jira_result = client.create_ticket(
                    summary=summary,
                    description=description,
                    customer_email=self._sender_email(payload),
                    priority=payload.get("priority_hint"),
                    payload_data=payload,
                )
            except Exception as exc:
                raise AppError("JIRA_REQUEST_FAILED", str(exc), status_code=502) from exc
            return {
                "ticket_system": "jira",
                "jira_issue_key": jira_result.get("issueKey"),
                "ticket_id": jira_result.get("issueKey"),
                "correlation_id": correlation_id,
                "sn_sys_id": None,
                "jira_request_fields": jira_result.get("requestFieldValues"),
            }

        if backend == "servicenow":
            if client is None:
                raise AppError("SN_DISABLED", "ServiceNow integration is not configured", status_code=503)
            try:
                sn_result = client.create_incident(payload)
            except Exception as exc:
                raise AppError("SN_TIMEOUT", str(exc), status_code=502) from exc
            payload_ref = sn_result.get("payload", {})
            ticket_id = payload_ref.get("sys_id") or str(uuid.uuid4())
            return {
                "ticket_system": "servicenow",
                "ticket_id": ticket_id,
                "sn_sys_id": ticket_id,
                "correlation_id": correlation_id,
            }

        raise AppError("UNSUPPORTED_BACKEND", f"Unsupported incident backend: {backend}", status_code=400)

    def ingest(self, payload: Dict[str, Any], idem_key: str | None = None) -> Dict[str, Any]:
        if idem_key and idem_key in self.idempotency_store:
            return self.idempotency_store[idem_key]

        key = self._build_key(payload)
        duplicate_result = None
        if hasattr(self.dedupe, "find_duplicate"):
            duplicate_result = self.dedupe.find_duplicate(key, payload)
        elif self.dedupe.is_duplicate(key, payload):
            duplicate_result = {"status": "duplicate"}

        if duplicate_result:
            result = {
                "status": "duplicate",
                "action": "merge",
                "now": self._now(),
                "ticket_system": duplicate_result.get("ticket_system") or self._ticket_backend(payload),
                "ticket_id": duplicate_result.get("ticket_id"),
                "sn_sys_id": duplicate_result.get("sn_sys_id"),
                "jira_issue_key": duplicate_result.get("jira_issue_key"),
                "correlation_id": duplicate_result.get("correlation_id"),
                "idem_key": idem_key,
            }
        else:
            correlation_id = str(uuid.uuid4())
            ticket_result = self._create_ticket(payload, correlation_id)
            result = {
                "status": "accepted",
                "action": "create",
                "now": self._now(),
                "idem_key": idem_key,
                **ticket_result,
            }

            if hasattr(self.dedupe, "remember"):
                self.dedupe.remember(key, payload, result)

        if idem_key:
            self.idempotency_store[idem_key] = result

        return result
