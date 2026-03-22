from typing import Any, Dict


class ServiceNowClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def create_incident(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "not_implemented"}
