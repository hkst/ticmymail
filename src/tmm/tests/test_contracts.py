import os
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from tmm.api.http_app import app
from tmm.config.loader import ConfigLoader
from tmm.service.dedupe_engine import ResourceNotFoundError, ResourceModifiedError


@pytest.fixture(scope="session")
def config_loader(tmp_path_factory):
    cfg = tmp_path_factory.mktemp("config")
    (cfg / "app.json").write_text(json.dumps({"config_version": "v1"}), encoding="utf-8")
    (cfg / "schema").mkdir(parents=True, exist_ok=True)
    (cfg / "schema" / "v1").mkdir(parents=True, exist_ok=True)
    (cfg / "schema" / "v1" / "schema.json").write_text(
        json.dumps({"title": "tmm-provider-schema-v1"}), encoding="utf-8"
    )
    (cfg / "dedupe").mkdir(parents=True, exist_ok=True)
    (cfg / "dedupe" / "v1").mkdir(parents=True, exist_ok=True)
    (cfg / "dedupe" / "v1" / "dedupe.rules.json").write_text(
        json.dumps({"dedupe_fields": ["message_id"]}), encoding="utf-8"
    )
    (cfg / "email").mkdir(parents=True, exist_ok=True)
    (cfg / "email" / "provider.json").write_text(
        json.dumps({
            "type": "smtp_relay",
            "retry_policy": {"max_attempts": 2, "backoff_seconds": 0},
            "smtp": {"host": "localhost", "port": 587},
        }),
        encoding="utf-8",
    )
    (cfg / "email" / "wrapper.md").write_text("{{ body }}\n\n---\nFooter", encoding="utf-8")
    (cfg / "email" / "templates").mkdir(parents=True, exist_ok=True)
    (cfg / "email" / "templates" / "status.md").write_text("Status: {{body}}", encoding="utf-8")
    os.environ["TMM_CONFIG_ROOT"] = str(cfg)
    yield ConfigLoader(str(cfg))
    os.environ.pop("TMM_CONFIG_ROOT", None)


@pytest.fixture
def client():
    return TestClient(app)


def test_ingest_idempotency(client):
    payload = {
        "schema_version": "v1",
        "event_type": "new",
        "message_id": "<mid1@example.com>",
        "thread_id": "<tid@example.com>",
        "subject": "test",
        "body": "hello",
        "sender": "alice@example.com",
    }
    headers = {"Idempotency-Key": "idem-key-123"}

    r1 = client.post("/v1/incidents/ingest", json=payload, headers=headers)
    r2 = client.post("/v1/incidents/ingest", json=payload, headers=headers)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["sn_sys_id"] == r2.json()["sn_sys_id"]
    assert r1.json()["status"] == r2.json()["status"]


def test_email_threading_headers(client):
    payload = {
        "to": "bob@example.com",
        "subject": "Hello",
        "body": "Hi",
        "message_id": "<msgid@example.com>",
        "thread_id": "<thread@example.com>",
    }
    r = client.post("/v1/comm/email", json=payload)

    assert r.status_code == 200
    data = r.json()
    assert data["in_reply_to"] == payload["message_id"]
    assert data["references"] == payload["thread_id"]


def test_email_template_and_wrapper(client):
    payload = {
        "to": "bob@example.com",
        "subject": "Hello",
        "template_key": "status",
        "body": "ok",
        "message_id": "<msgid2@example.com>",
        "thread_id": "<thread2@example.com>",
    }

    r = client.post("/v1/comm/email", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["provider"] == "smtp_relay" or data["provider"] == "graph_send_only" or data["status"] == "sent"

    # ensure wrapper applied from config/email/wrapper.md
    assert "ticmymail Part‑2 service" in data["message"]["body"]
    assert "Current state" in data["message"]["body"]


def test_servicenow_create_and_comment(client):
    payload = {"subject": "Test", "body": "Hello", "sender": "alice"}
    r = client.post("/v1/integrations/servicenow/incidents", json=payload) 
    assert r.status_code == 200
    assert r.json()["operation"] == "create"

    sys_id = "sys123"
    r2 = client.post(f"/v1/integrations/servicenow/incidents/{sys_id}/comment", json={"comment": "Note"})
    assert r2.status_code == 200
    assert r2.json()["operation"] == "comment"


def test_bigpanda_post_and_search_and_correlate(client):
    payload = [
        {"host": "h1", "service": "svc", "status": "critical", "description": "d", "tags": ["t1"]}
    ]
    r = client.post("/v1/integrations/bigpanda/events", json=payload)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    q = {"tags": ["t1"], "service": "svc"}
    r2 = client.post("/v1/integrations/bigpanda/search", json=q)
    assert r2.status_code == 200
    assert r2.json()["ok"] is True

    r3 = client.post("/v1/integrations/bigpanda/correlate", json={"alert_id": "sim-1", "correlation_ids": ["cid1"]})
    assert r3.status_code == 200
    assert r3.json()["operation"] == "attach_correlation"


class FakeBlobClient:
    def __init__(self):
        self._data = b""
        self.exists = False
        self.etag = None
        self.conflict_next_upload = False

    def download_blob(self):
        if not self.exists:
            raise ResourceNotFoundError()

        class FakeDownloader:
            def __init__(self, data):
                self._data = data

            def readall(self):
                return self._data

        return FakeDownloader(self._data)

    def get_blob_properties(self):
        if not self.exists:
            raise ResourceNotFoundError()
        return type("P", (), {"etag": self.etag})()

    def upload_blob(self, data, overwrite=True, if_match=None):
        if self.conflict_next_upload:
            self.conflict_next_upload = False
            # Simulate another process writing the same new hash concurrently
            remote_state = json.loads(data.decode("utf-8"))
            if "hashes" in remote_state:
                self._data = json.dumps({"hashes": list(remote_state["hashes"])}).encode("utf-8")
                self.exists = True
                self.etag = '"1"'
            raise ResourceModifiedError("Simulated ResourceModifiedError")

        if if_match is not None and self.exists and if_match != self.etag:
            raise ResourceModifiedError("Simulated ResourceModifiedError")

        self._data = data
        self.exists = True
        self.etag = '"1"'


def test_adls_dedupe_engine_conflict_no_duplicate(tmp_path):
    app_cfg = {
        "dedupe": {"backend": "adls", "write_attempts": 2, "cache_ttl_seconds": 1, "reconcile_interval_seconds": 1},
        "adls_dedupe": {"container": "dedupe", "blob_path": "dedupe-state.json", "connection_string": "fake"},
    }
    fake_blob = FakeBlobClient()
    engine = ADLSDedupeEngine(app_cfg, blob_client=fake_blob)

    payload = {"subject": "test", "body": "hello"}
    # first call should write and return False (not duplicate)
    assert engine.is_duplicate("k1", payload) is False

    # second call same key should be duplicate
    assert engine.is_duplicate("k1", payload) is True

    # simulate lease/write conflict on a different key (commit happened in between)
    fake_blob.conflict_next_upload = True
    new_payload = {"subject": "test2", "body": "hello2"}
    # because conflict triggers remote refresh and remote now contains this key, should become duplicate
    result = engine.is_duplicate("k2", new_payload)
    assert result is True


def test_version_contains_config_versions(client, config_loader):
    r = client.get("/v1/version")
    assert r.status_code == 200
    data = r.json()
    assert data["service_version"] == "0.1.0"
    assert data["app_config_version"] == "v1"
    assert data["schema_version"] == "v1"
    assert data["dedupe_rules_version"] == "v1"
