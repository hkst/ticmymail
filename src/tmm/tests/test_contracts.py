import os
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from tmm.api.http_app import app
from tmm.config.loader import ConfigLoader


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


def test_version_contains_config_versions(client, config_loader):
    r = client.get("/v1/version")
    assert r.status_code == 200
    data = r.json()
    assert data["service_version"] == "0.1.0"
    assert data["app_config_version"] == "v1"
    assert data["schema_version"] == "v1"
    assert data["dedupe_rules_version"] == "v1"
