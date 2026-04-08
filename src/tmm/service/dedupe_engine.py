import hashlib
import json
import time
from typing import Any, Dict, Optional, Set

try:
    from azure.storage.blob import BlobServiceClient
    from azure.core.exceptions import ResourceNotFoundError, ResourceModifiedError
except ImportError:
    BlobServiceClient = None  # type: ignore
    ResourceNotFoundError = FileNotFoundError  # type: ignore
    ResourceModifiedError = RuntimeError  # type: ignore


class DedupeEngine:
    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        self.rules = rules or {}
        self._seen: Dict[str, Dict[str, Any]] = {}

    def _dedupe_fields(self) -> list[str]:
        return list(self.rules.get("dedupe_fields", ["message_id", "thread_id", "subject", "body"]))

    @staticmethod
    def _normalize_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return "|".join(DedupeEngine._normalize_value(item) for item in value)
        if isinstance(value, dict):
            return json.dumps(value, sort_keys=True)
        return " ".join(str(value).strip().lower().split())

    def build_hash(self, key: str, payload: Dict[str, Any]) -> str:
        normalized_fields = {
            field: self._normalize_value(payload.get(field))
            for field in self._dedupe_fields()
        }
        if not any(normalized_fields.values()):
            normalized_fields["fallback_key"] = self._normalize_value(key)

        normalized = json.dumps(normalized_fields, sort_keys=True)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def find_duplicate(self, key: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._seen.get(self.build_hash(key, payload))

    def remember(self, key: str, payload: Dict[str, Any], result: Dict[str, Any]) -> None:
        self._seen[self.build_hash(key, payload)] = dict(result)

    def is_duplicate(self, key: str, payload: Dict[str, Any]) -> bool:
        duplicate = self.find_duplicate(key, payload)
        if duplicate is not None:
            return True
        self.remember(key, payload, {"status": "accepted"})
        return False


class ADLSDedupeEngine:
    def __init__(
        self,
        app_config: Dict[str, Any],
        blob_client: Optional[Any] = None,
        blob_service_client: Optional[Any] = None,
    ):
        dedupe_cfg = app_config.get("dedupe", {})
        self.cache_ttl = int(dedupe_cfg.get("cache_ttl_seconds", 300))
        self.reconcile_interval = int(dedupe_cfg.get("reconcile_interval_seconds", 300))

        self._cache: Set[str] = set()
        self._cache_epoch = 0.0
        self._last_reconcile = 0.0

        self.app_config = app_config
        self._adls_cfg = app_config.get("adls_dedupe", {})
        self.container_name = self._adls_cfg.get("container", "dedupe")
        self.blob_path = self._adls_cfg.get("blob_path", "dedupe-state.json")
        self.connection_string = self._adls_cfg.get("connection_string")

        if blob_client is not None:
            self._blob_client = blob_client
        else:
            if blob_service_client is not None:
                service = blob_service_client
            else:
                if BlobServiceClient is None:
                    raise RuntimeError("azure-storage-blob is required for ADLSDedupeEngine")
                if not self.connection_string:
                    raise ValueError("ADLS dedupe configuration must have connection_string")
                service = BlobServiceClient.from_connection_string(self.connection_string)
            self._blob_client = service.get_blob_client(container=self.container_name, blob=self.blob_path)

    def _dedupe_fields(self) -> list[str]:
        return list(self.app_config.get("dedupe", {}).get("dedupe_fields", ["message_id", "thread_id", "subject", "body"]))

    @staticmethod
    def _normalize_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return "|".join(ADLSDedupeEngine._normalize_value(item) for item in value)
        if isinstance(value, dict):
            return json.dumps(value, sort_keys=True)
        return " ".join(str(value).strip().lower().split())

    def build_hash(self, key: str, payload: Dict[str, Any]) -> str:
        normalized_fields = {
            field: self._normalize_value(payload.get(field))
            for field in self._dedupe_fields()
        }
        if not any(normalized_fields.values()):
            normalized_fields["fallback_key"] = self._normalize_value(key)
        normalized = json.dumps(normalized_fields, sort_keys=True)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _now(self) -> float:
        return time.time()

    def _refresh_cache(self) -> None:
        now = self._now()
        if now - self._cache_epoch < self.cache_ttl:
            return

        self._cache = self._load_remote_state()
        self._cache_epoch = now

    def _load_remote_state(self) -> Set[str]:
        try:
            downloader = self._blob_client.download_blob()
            data = downloader.readall().decode("utf-8")
            payload = json.loads(data)
            return set(payload.get("hashes", []))
        except (ResourceNotFoundError, FileNotFoundError):
            return set()

    def _write_remote_state(self, hashes: Set[str], etag: Optional[str] = None) -> None:
        body = json.dumps({"hashes": sorted(list(hashes))}).encode("utf-8")
        kwargs = {}

        if etag:
            kwargs["if_match"] = etag

        # upload_blob does overwrite semantics, use if_match for concurrency guard
        self._blob_client.upload_blob(body, overwrite=True, **kwargs)

    def _get_remote_etag(self) -> Optional[str]:
        try:
            props = self._blob_client.get_blob_properties()
            return props.etag
        except ResourceNotFoundError:
            return None

    def find_duplicate(self, key: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        self._refresh_cache()
        hash_value = self.build_hash(key, payload)
        if hash_value in self._cache:
            return {"fingerprint": hash_value}

        remote_set = self._load_remote_state()
        if hash_value in remote_set:
            self._cache = remote_set
            self._cache_epoch = self._now()
            return {"fingerprint": hash_value}

        return None

    def remember(self, key: str, payload: Dict[str, Any], result: Dict[str, Any]) -> bool:
        hash_value = self.build_hash(key, payload)

        max_attempts = int(self.app_config.get("dedupe", {}).get("write_attempts", 3))
        for _ in range(max_attempts):
            remote_set = self._load_remote_state()
            if hash_value in remote_set:
                self._cache = remote_set
                self._cache_epoch = self._now()
                return True

            remote_set.add(hash_value)
            etag = self._get_remote_etag()

            try:
                self._write_remote_state(remote_set, etag=etag)
                self._cache = remote_set
                self._cache_epoch = self._now()
                return False
            except ResourceModifiedError:
                continue

        self._cache = self._load_remote_state()
        self._cache_epoch = self._now()
        return hash_value in self._cache

    def is_duplicate(self, key: str, payload: Dict[str, Any]) -> bool:
        if self.find_duplicate(key, payload) is not None:
            return True
        return bool(self.remember(key, payload, {"status": "accepted"}))

    def reconcile(self) -> None:
        now = self._now()
        if now - self._last_reconcile < self.reconcile_interval:
            return

        remote_set = self._load_remote_state()
        merged = self._cache.union(remote_set)
        etag = self._get_remote_etag()

        self._write_remote_state(merged, etag=etag)
        self._cache = merged
        self._cache_epoch = now
        self._last_reconcile = now
