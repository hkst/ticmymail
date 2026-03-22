from typing import Any, Dict


class DedupeEngine:
    def __init__(self):
        self._seen = set()

    def is_duplicate(self, key: str, payload: Dict[str, Any]) -> bool:
        if key in self._seen:
            return True
        # stub behavior for now
        self._seen.add(key)
        return False
