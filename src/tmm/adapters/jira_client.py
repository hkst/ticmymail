import json
from datetime import datetime
from typing import Dict, Any, Optional

import requests

class JiraClient:
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config["base_url"]
        self.auth = (config["email"], config["api_token"])
        self.service_desk_id = config["service_desk_id"]
        self.request_type_id = config["request_type_id"]
        self.timeout_seconds = int(config.get("timeout_seconds", 30))
        self.dry_run = bool(config.get("dry_run", False))
        self.raise_on_behalf_of = bool(config.get("raise_on_behalf_of", False))
        self.include_priority = bool(config.get("include_priority", False))
        self.field_map = dict(config.get("request_field_map", {}))
        self.date_fields = set(config.get("date_fields", []))

    @staticmethod
    def _as_date(value: Any) -> Optional[str]:
        if value in (None, ""):
            return None

        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")

        text = str(value).strip()
        if not text:
            return None

        if "T" in text:
            text = text.split("T", 1)[0]

        if " " in text:
            text = text.split(" ", 1)[0]

        return text

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned if cleaned else None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=True)
        return value

    def _build_request_field_values(
        self,
        summary: str,
        description: str,
        priority: Optional[str],
        payload_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        request_field_values: Dict[str, Any] = {
            "summary": summary,
            "description": description,
        }

        if priority and self.include_priority:
            request_field_values["priority"] = priority

        payload_data = payload_data or {}
        for payload_key, jira_field_id in self.field_map.items():
            raw_value = payload_data.get(payload_key)
            if payload_key in self.date_fields:
                mapped_value = self._as_date(raw_value)
            else:
                mapped_value = self._normalize_value(raw_value)

            if mapped_value is not None:
                request_field_values[jira_field_id] = mapped_value

        return request_field_values

    def create_ticket(
        self,
        summary: str,
        description: str,
        customer_email: Optional[str] = None,
        priority: Optional[str] = None,
        payload_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        clean_customer_email = customer_email.strip() if isinstance(customer_email, str) else customer_email
        request_field_values = self._build_request_field_values(summary, description, priority, payload_data)

        if self.dry_run:
            issue_key = f"SIM-{abs(hash((summary, clean_customer_email, priority))) % 100000}"
            return {
                "issueKey": issue_key,
                "status": "simulated",
                "requestFieldValues": request_field_values,
            }

        url = f"{self.base_url}/rest/servicedeskapi/request"
        payload = {
            "serviceDeskId": self.service_desk_id,
            "requestTypeId": self.request_type_id,
            "requestFieldValues": request_field_values,
        }
        if clean_customer_email and self.raise_on_behalf_of:
            payload["raiseOnBehalfOf"] = clean_customer_email

        response = requests.post(
            url,
            json=payload,
            auth=self.auth,
            timeout=self.timeout_seconds,
            headers={"X-ExperimentalApi": "opt-in"},
        )
        if not response.ok:
            raise requests.HTTPError(
                f"Jira request failed with status {response.status_code}: {response.text}",
                response=response,
            )
        return response.json()

    def get_ticket(self, issue_key: str) -> Dict[str, Any]:
        url = f"{self.base_url}/rest/servicedeskapi/request/{issue_key}"
        response = requests.get(url, auth=self.auth, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

