# MVP demonstrator evidence

Date captured: 2026-04-08

This document provides log-based evidence for the MVP demonstrator requirements.

## 1) API endpoints responding (health/version/ingest/email/bigpanda)

Evidence source file:
- artifacts/evidence/mvp_endpoint_evidence.json

### /v1/health
```json
{
  "status": "ok"
}
```

### /v1/version
```json
{
  "service_version": "0.1.0",
  "app_config_version": "v1",
  "schema_version": "v1",
  "dedupe_rules_version": "v1",
  "incident_backend": "servicenow",
  "log_file": "logs\\run-20260408T102700.log"
}
```

### /v1/incidents/ingest
```json
{
  "status": "accepted",
  "action": "create",
  "idem_key": "evidence-idem-01",
  "ticket_system": "servicenow",
  "ticket_id": "9cf40b13-aaf6-4350-b624-8cd2652b859d",
  "sn_sys_id": "9cf40b13-aaf6-4350-b624-8cd2652b859d"
}
```

### /v1/comm/email
```json
{
  "sent": true,
  "status": "sent",
  "provider": "smtp_relay",
  "in_reply_to": "<evidence-msg@example.com>",
  "references": "<evidence-thread@example.com>"
}
```

### /v1/integrations/bigpanda/events and /search
```json
{
  "events": { "ok": true, "ref": "post_alert" },
  "search": { "ok": true }
}
```

## 2) Config files and versioning visible in /v1/version output

Evidence from /v1/version confirms config and versioning values:
- app_config_version: v1
- schema_version: v1
- dedupe_rules_version: v1
- incident_backend: servicenow
- nfr block is present
- log_file path is present

Related config files in repo:
- config/app.json
- config/schema/v1/schema.json
- config/dedupe/v1/dedupe.rules.json
- config/nfr.json

## 3) Idempotency: same payload does not create duplicate incident

Evidence from artifacts/evidence/mvp_endpoint_evidence.json:
- First ingest with Idempotency-Key evidence-idem-01 returned sn_sys_id: 9cf40b13-aaf6-4350-b624-8cd2652b859d
- Second ingest with the same Idempotency-Key returned the same sn_sys_id: 9cf40b13-aaf6-4350-b624-8cd2652b859d

Conclusion:
- No duplicate incident was created for repeated delivery of the same payload and same idempotency key.

## 4) Email response includes In-Reply-To and References and uses wrapper/footer

Evidence from artifacts/evidence/mvp_endpoint_evidence.json (email response):
```json
{
  "in_reply_to": "<evidence-msg@example.com>",
  "references": "<evidence-thread@example.com>",
  "message": {
    "body": "Classification: CONFIDENTIAL\n\nStatus update for incident: .\n\nCurrent state: .\n\n\n---\nThis message was sent by ticmymail Part-2 service.\n"
  }
}
```

Checks satisfied:
- In-Reply-To present
- References present
- Wrapper/footer present (separator and service footer text)

## 5) Unit tests green and CI run output

### Unit tests
Evidence file:
- artifacts/evidence/pytest_contracts_output_utf8.txt

Summary line:
```text
======================= 14 passed, 3 warnings in 0.43s ========================
```

### CI workflow output reference
CI workflow definition is present at:
- .github/workflows/ci.yml

Workflow includes:
- lint job (ruff)
- test job (pytest -q)
- build-and-artifacts job

Note:
- This evidence package includes a fresh local test run output file and the CI workflow definition. If needed, add a GitHub Actions run URL/screenshot from the latest run in your repository UI.

## Additional run log evidence

Run log referenced by /v1/version:
- logs/run-20260408T102700.log

Sample entries show endpoint activity:
- /v1/version outcome ok
- /v1/incidents/ingest outcome accepted (same idem key used twice)
- /v1/comm/email outcome sent
- /v1/integrations/bigpanda/events outcome posted
- /v1/integrations/bigpanda/search outcome found
