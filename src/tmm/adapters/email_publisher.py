from typing import Any, Dict


class EmailPublisher:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "not_implemented"}
