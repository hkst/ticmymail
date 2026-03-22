import json
from pathlib import Path
from fastapi.testclient import TestClient
from ticmymail.app import create_app


def _write_default_config(cfg_root: Path):
    (cfg_root / "integrations").mkdir(parents=True, exist_ok=True)
    (cfg_root / "email").mkdir(parents=True, exist_ok=True)
    (cfg_root / "email" / "templates").mkdir(parents=True, exist_ok=True)

    (cfg_root / "app.json").write_text(json.dumps({"dedupe_root": str(cfg_root / "dedupe")}), encoding="utf-8")
    (cfg_root / "schema").mkdir(parents=True, exist_ok=True)
    (cfg_root / "schema" / "v1.json").write_text("{}", encoding="utf-8")
    (cfg_root / "dedupe").mkdir(parents=True, exist_ok=True)
    (cfg_root / "dedupe" / "v1.json").write_text("{}", encoding="utf-8")
    (cfg_root / "integrations" / "servicenow.json").write_text("{}", encoding="utf-8")
    (cfg_root / "integrations" / "bigpanda.json").write_text(json.dumps({"api_token": "fake"}), encoding="utf-8")
    (cfg_root / "email" / "provider.json").write_text(json.dumps({"type": "mock"}), encoding="utf-8")
    (cfg_root / "email" / "wrapper.md").write_text("{{ body }}", encoding="utf-8")
    (cfg_root / "nfr.json").write_text("{}", encoding="utf-8")


def test_health_and_version(tmp_path: Path):
    _write_default_config(tmp_path)
    app = create_app(tmp_path)
    client = TestClient(app)

    resp = client.get("/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    resp = client.get("/v1/version")
    assert resp.status_code == 200
    assert "version" in resp.json()


def test_incident_ingest_dedupe(tmp_path: Path):
    _write_default_config(tmp_path)
    app = create_app(tmp_path)
    client = TestClient(app)

    payload = {"incident_id": "INC-100", "source": "test", "details": {"a": 1}}
    r1 = client.post("/v1/incidents/ingest", json=payload)
    assert r1.status_code == 200
    assert r1.json()["status"] == "accepted"

    r2 = client.post("/v1/incidents/ingest", json=payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate"


def test_bigpanda_event(tmp_path: Path):
    _write_default_config(tmp_path)
    app = create_app(tmp_path)
    client = TestClient(app)

    payload =[{
        "host": "test-host",
        "service": "test-service",
        "status": "critical",
        "description": "desc"
    }]
    resp = client.post("/v1/integrations/bigpanda/events", json=payload)
    assert resp.status_code == 200
    assert resp.json()["results"][0]["status"] == "accepted"


def test_comm_email_requirements(tmp_path: Path):
    _write_default_config(tmp_path)
    app = create_app(tmp_path)
    client = TestClient(app)

    payload = {
        "from": "foo@example.com",
        "to": "bar@example.com",
        "subject": "hi",
        "body": "test",
        "message_id": "<msgid@example.com>",
        "thread_id": "<thread@example.com>"
    }
    resp = client.post("/v1/comm/email", json=payload)
    assert resp.status_code == 200
    assert resp.json()["provider"] == "mock"
