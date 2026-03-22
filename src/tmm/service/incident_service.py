import uuid
from typing import Any, Dict


class IncidentService:
    def __init__(self, dedupe_engine):
        self.dedupe = dedupe_engine
        self.idempotency_store: Dict[str, Dict[str, Any]] = {}

    def ingest(self, payload: Dict[str, Any], idem_key: str | None = None) -> Dict[str, Any]:
        if idem_key and idem_key in self.idempotency_store:
            return self.idempotency_store[idem_key]

        key = f"{payload.get('message_id')}|{payload.get('thread_id')}"
        is_dup = self.dedupe.is_duplicate(key, payload)

        if is_dup:
            result = {
                "status": "duplicate",
                "sn_sys_id": None,
                "correlation_id": None,
                "idem_key": idem_key,
            }
        else:
            sn_sys_id = str(uuid.uuid4())
            result = {
                "status": "accepted",
                "sn_sys_id": sn_sys_id,
                "correlation_id": str(uuid.uuid4()),
                "idem_key": idem_key,
            }

        if idem_key:
            self.idempotency_store[idem_key] = result

        return result
