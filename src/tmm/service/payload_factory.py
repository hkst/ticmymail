import copy
from typing import Any, Dict, List


class PayloadScenarioFactory:
    def __init__(self, sample_payload: Dict[str, Any]):
        self.sample_payload = sample_payload

    def _base_event(self) -> Dict[str, Any]:
        return copy.deepcopy(self.sample_payload["value"][0])

    @staticmethod
    def _sender(index: int) -> Dict[str, Any]:
        return {
            "emailAddress": {
                "name": f"Acme User {index:02d}",
                "address": f"marketrisk.user{index:02d}@acmebank.example.com",
            }
        }

    def build_variations(self, count: int = 30) -> List[Dict[str, Any]]:
        issue_variations = [
            ("VaR analytics batch delay", "new", "high"),
            ("Reporting platform stale positions", "new", "high"),
            ("Data reconciliation mismatch", "new", "normal"),
            ("Intraday risk cube refresh failed", "new", "high"),
            ("Scenario results missing for EMEA", "new", "normal"),
            ("Limit dashboard latency spike", "status", "normal"),
            ("PnL attribution report not loading", "new", "high"),
            ("Counterparty hierarchy feed incomplete", "reply", "normal"),
            ("Historical VaR extract mismatch", "new", "normal"),
            ("Overnight risk pipeline timeout", "escalate", "high"),
        ]

        payloads: List[Dict[str, Any]] = []
        for index in range(count):
            issue_title, event_type, importance = issue_variations[index % len(issue_variations)]
            event = self._base_event()
            event["id"] = f"<acme-market-risk-{index + 1}@tmm.local>"
            event["conversationId"] = f"<acme-thread-{index + 1}@tmm.local>"
            event["event_type"] = event_type
            event["importance"] = importance
            event["from"] = self._sender(index + 1)
            event["subject"] = f"Acme Market Risk: {issue_title} on Data, VaR analytics and reporting platform"
            event["bodyPreview"] = (
                "Business is investment bank Acme and market risk division users are raising issues with "
                f"Data, VaR analytics and reporting platform. Scenario {index + 1}: {issue_title.lower()}."
            )
            event["attachments"] = [
                {
                    "name": f"evidence-{index + 1:02d}.txt",
                    "uri": f"https://acme.example.com/evidence/{index + 1:02d}",
                    "contentType": "text/plain",
                }
            ]
            event["correlation_hints"] = [
                "Acme",
                "MarketRisk",
                "DataPlatform",
                f"scenario-{index + 1:02d}",
            ]
            event["business"] = "Acme Investment Bank"
            event["division"] = "Market Risk"
            event["platform"] = "Data, VaR analytics and reporting platform"
            event["target_system"] = "jira"

            payloads.append(
                {
                    "schema_version": "v1",
                    "@odata.context": self.sample_payload.get("@odata.context"),
                    "value": [event],
                }
            )

        return payloads

    def build_duplicate_demo(self) -> List[Dict[str, Any]]:
        payloads = self.build_variations(5)
        duplicate_one = copy.deepcopy(payloads[0])
        duplicate_one["value"][0]["id"] = "<acme-market-risk-dup-1@tmm.local>"
        duplicate_one["value"][0]["conversationId"] = "<acme-thread-dup-1@tmm.local>"

        duplicate_two = copy.deepcopy(payloads[0])
        duplicate_two["value"][0]["id"] = "<acme-market-risk-dup-2@tmm.local>"
        duplicate_two["value"][0]["conversationId"] = "<acme-thread-dup-2@tmm.local>"

        duplicate_three = copy.deepcopy(payloads[2])
        duplicate_three["value"][0]["id"] = "<acme-market-risk-dup-3@tmm.local>"
        duplicate_three["value"][0]["conversationId"] = "<acme-thread-dup-3@tmm.local>"

        return [payloads[0], duplicate_one, duplicate_two, payloads[1], payloads[2], duplicate_three]

    def build_escalation_demo(self) -> Dict[str, Any]:
        """Single high-priority escalation payload routed to Jira."""
        event = self._base_event()
        event["id"] = "<acme-escalation-001@tmm.local>"
        event["conversationId"] = "<acme-escalation-thread-001@tmm.local>"
        event["event_type"] = "escalate"
        event["importance"] = "high"
        event["from"] = self._sender(99)
        event["subject"] = "ESCALATION: Intraday VaR limit breach — immediate action required"
        event["bodyPreview"] = (
            "Business is investment bank Acme and market risk division. "
            "Intraday VaR limit has been breached on the EMEA trading book. "
            "Risk systems are not publishing live risk numbers. Escalation required."
        )
        event["attachments"] = [
            {
                "name": "breach-report-001.pdf",
                "uri": "https://acme.example.com/reports/breach-001",
                "contentType": "application/pdf",
            }
        ]
        event["correlation_hints"] = ["Acme", "MarketRisk", "VaR", "LimitBreach", "Escalation"]
        event["business"] = "Acme Investment Bank"
        event["division"] = "Market Risk"
        event["platform"] = "Data, VaR analytics and reporting platform"
        event["target_system"] = "jira"
        event["dept_name"] = "EMEA Market Risk"
        event["external_ref"] = "ACME-ESC-001"
        event["data_domain"] = "VaR"
        return {
            "schema_version": "v1",
            "@odata.context": self.sample_payload.get("@odata.context"),
            "value": [event],
        }

    def build_servicenow_demo(self) -> Dict[str, Any]:
        """Single payload explicitly routed to ServiceNow."""
        event = self._base_event()
        event["id"] = "<acme-sn-demo-001@tmm.local>"
        event["conversationId"] = "<acme-sn-thread-001@tmm.local>"
        event["event_type"] = "new"
        event["importance"] = "normal"
        event["from"] = self._sender(50)
        event["subject"] = "Acme Market Risk: Overnight batch output missing from data warehouse"
        event["bodyPreview"] = (
            "Business is investment bank Acme and market risk division. "
            "Overnight risk batch did not populate the data warehouse. "
            "Downstream reporting systems are showing stale data from previous day."
        )
        event["attachments"] = []
        event["correlation_hints"] = ["Acme", "MarketRisk", "DataWarehouse", "OvernightBatch"]
        event["business"] = "Acme Investment Bank"
        event["division"] = "Market Risk"
        event["platform"] = "Data, VaR analytics and reporting platform"
        event["target_system"] = "servicenow"
        return {
            "schema_version": "v1",
            "@odata.context": self.sample_payload.get("@odata.context"),
            "value": [event],
        }

    def build_limit_breach_demo(self) -> Dict[str, Any]:
        """Intraday limit monitoring failure with full custom field metadata."""
        event = self._base_event()
        event["id"] = "<acme-limit-breach-001@tmm.local>"
        event["conversationId"] = "<acme-limit-thread-001@tmm.local>"
        event["event_type"] = "new"
        event["importance"] = "high"
        event["from"] = self._sender(77)
        event["subject"] = "Acme Market Risk: Limit dashboard stale — intraday monitoring gap"
        event["bodyPreview"] = (
            "Business is investment bank Acme and market risk division. "
            "The intraday limit monitoring dashboard has been stale for 90 minutes. "
            "Traders cannot see live limit utilisation. Risk team escalating."
        )
        event["attachments"] = [
            {
                "name": "limit-gap-evidence.csv",
                "uri": "https://acme.example.com/evidence/limit-gap-001",
                "contentType": "text/csv",
            }
        ]
        event["correlation_hints"] = ["Acme", "MarketRisk", "LimitMonitoring", "Intraday"]
        event["business"] = "Acme Investment Bank"
        event["division"] = "Market Risk"
        event["platform"] = "Data, VaR analytics and reporting platform"
        event["target_system"] = "jira"
        event["dept_name"] = "Global Market Risk"
        event["external_ref"] = "ACME-LIM-2026-04"
        event["data_domain"] = "Limits"
        return {
            "schema_version": "v1",
            "@odata.context": self.sample_payload.get("@odata.context"),
            "value": [event],
        }