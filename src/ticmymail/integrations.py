from typing import Any, Dict


class BigPandaError(RuntimeError):
    pass


class BigPandaClient:
    def __init__(self, config: Dict[str, Any]):
        self._config = config

    def send_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        api_token = self._config.get("api_token")
        if not api_token:
            raise BigPandaError("bigpanda api_token required")

        # Placeholder for calling real BigPanda API. Here we simply echo.
        return {
            "status": "accepted",
            "event": event,
            "sent_with_mock": True,
        }
