from typing import Any, Dict


class BigPandaClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def send_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "not_implemented"}
