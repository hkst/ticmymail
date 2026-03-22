import hashlib
import json
import threading
from pathlib import Path
from typing import Optional


class DedupeError(RuntimeError):
    pass


class DedupeStoreProtocol:
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def persist(self, key: str) -> None:
        raise NotImplementedError

    def acquire_lock(self, key: str) -> bool:
        raise NotImplementedError

    def release_lock(self, key: str) -> None:
        raise NotImplementedError


class InMemoryDedupeStore(DedupeStoreProtocol):
    def __init__(self):
        self._keys = set()
        self._locks = {}
        self._mutex = threading.RLock()

    def exists(self, key: str) -> bool:
        with self._mutex:
            return key in self._keys

    def persist(self, key: str) -> None:
        with self._mutex:
            self._keys.add(key)

    def acquire_lock(self, key: str) -> bool:
        with self._mutex:
            if self._locks.get(key, False):
                return False
            self._locks[key] = True
            return True

    def release_lock(self, key: str) -> None:
        with self._mutex:
            self._locks.pop(key, None)


class ADLSDedupeStore(DedupeStoreProtocol):
    """Stub ADLS-backed dedupe state (local file path emulation)."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index = self.root / "dedupe_index.json"
        if not self.index.exists():
            self.index.write_text(json.dumps({}), encoding="utf-8")
        self._lock = threading.RLock()

    def _read(self) -> dict:
        return json.loads(self.index.read_text(encoding="utf-8") or "{}")

    def _write(self, data: dict) -> None:
        self.index.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def exists(self, key: str) -> bool:
        with self._lock:
            data = self._read()
            return key in data

    def persist(self, key: str) -> None:
        with self._lock:
            data = self._read()
            data[key] = True
            self._write(data)

    def acquire_lock(self, key: str) -> bool:
        # ETag-style guard with a lock file
        with self._lock:
            lockfile = self.root / f"{key}.lock"
            if lockfile.exists():
                return False
            lockfile.write_text("locked", encoding="utf-8")
            return True

    def release_lock(self, key: str) -> None:
        with self._lock:
            lockfile = self.root / f"{key}.lock"
            if lockfile.exists():
                lockfile.unlink()


class DedupeService:
    def __init__(self, store: DedupeStoreProtocol):
        self.store = store

    @staticmethod
    def make_key(incident_id: str, alert_hash: Optional[str] = None) -> str:
        base = incident_id if not alert_hash else f"{incident_id}:{alert_hash}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def is_duplicate(self, incident_id: str, incident_body: dict) -> bool:
        key = self.make_key(incident_id, hashlib.sha256(json.dumps(incident_body, sort_keys=True).encode("utf-8")).hexdigest())
        if self.store.exists(key):
            return True
        if not self.store.acquire_lock(key):
            # concurrent in-flight, treat as duplicate-safe and stop processing
            return True
        try:
            if self.store.exists(key):
                return True
            self.store.persist(key)
            return False
        finally:
            self.store.release_lock(key)
