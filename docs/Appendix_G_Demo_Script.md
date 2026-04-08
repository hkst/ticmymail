# Appendix G - Demo script (recording guide)

Use this script for your project MVP recording and upload the final video to OneDrive or SharePoint.

## Recording objective

Demonstrate the Part-2 MVP capabilities end to end:
- API availability and config loading
- Idempotent incident ingestion
- Email template wrapping and threading
- BigPanda event and correlation flow
- Business impact summary

## Pre-record checklist (2-3 minutes)

1. Open the repo root in VS Code.
2. Open these folders in the explorer so they are visible on screen:
- config/schema
- config/dedupe
- config/integrations
- config/email/templates
- config/nfr.json
3. Start the service if not already running.

PowerShell command:
```powershell
Set-Location "C:\Users\henley\Documents\Dev\mypy\ticmymail"
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m uvicorn tmm.api.http_app:app --host 127.0.0.1 --port 8000
```

Keep this terminal open while recording.

## Demo flow (talk track + commands)

Base URL used below:
```text
http://127.0.0.1:8000
```

### 1) Show config structure in repository

Narration:
- "I am showing the configuration-driven design: schema, dedupe rules, integration configs, email templates, and NFR controls."

On screen:
- Expand config/schema/v1/schema.json
- Expand config/dedupe/v1/dedupe.rules.json
- Expand config/integrations/jira.json, servicenow.json, bigpanda.json
- Expand config/email/templates/status.md and config/email/wrapper.md
- Open config/nfr.json

### 2) Call health and version endpoints

Narration:
- "Now I verify service health and show loaded configuration/version metadata."

Commands:
```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/v1/health" | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/v1/version" | ConvertTo-Json -Depth 10
```

What to highlight in version output:
- service_version
- app_config_version
- schema_version
- dedupe_rules_version
- incident_backend
- nfr block
- log_file path

### 3) Idempotency demo: ingest same payload twice with same idempotency key

Narration:
- "I submit the same incident payload twice with the same Idempotency-Key and show no duplicate ticket is created."

Commands:
```powershell
$headers = @{ "Idempotency-Key" = "demo-idem-appendix-g-001" }
$payload = @{
  schema_version = "v1"
  event_type = "new"
  message_id = "<appendixg-mid-001@example.com>"
  thread_id = "<appendixg-thread-001@example.com>"
  subject = "Appendix G idempotency evidence"
  body = "Repeated submission should not create duplicate incident"
  sender = "appendixg@example.com"
}

$r1 = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/v1/incidents/ingest" -Headers $headers -Body ($payload | ConvertTo-Json -Depth 10) -ContentType "application/json"
$r2 = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/v1/incidents/ingest" -Headers $headers -Body ($payload | ConvertTo-Json -Depth 10) -ContentType "application/json"

"FIRST:";  $r1 | ConvertTo-Json -Depth 10
"SECOND:"; $r2 | ConvertTo-Json -Depth 10
```

What to highlight:
- Same ticket_id and same sn_sys_id (or same jira_issue_key if routed to Jira)
- Same idem_key
- No duplicate ticket reference

### 4) Email demo: template, wrapper/footer, threading headers

Narration:
- "Next I send an outbound email using a template and show threading headers and wrapper/footer content in the response."

Commands:
```powershell
$emailPayload = @{
  to = "stakeholder@example.com"
  subject = "Appendix G email demo"
  template_key = "status"
  body = "Fallback body"
  message_id = "<appendixg-msg-001@example.com>"
  thread_id = "<appendixg-thread-001@example.com>"
  classification = "CONFIDENTIAL"
  variables = @{
    incident_id = "INC-APPENDIX-G-001"
    state = "Investigating"
  }
  footer_flag = $true
}

$emailResponse = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/v1/comm/email" -Body ($emailPayload | ConvertTo-Json -Depth 10) -ContentType "application/json"
$emailResponse | ConvertTo-Json -Depth 10
```

What to highlight:
- in_reply_to exists
- references exists
- message.body includes wrapper/footer text and classification line

Optional log view:
```powershell
Get-Content .\logs\run-*.log | Select-String "/v1/comm/email" | Select-Object -Last 3
```

### 5) BigPanda demo: events + correlation response handling

Narration:
- "Now I post a BigPanda event and then call correlate to demonstrate correlation response handling in the integration layer."

Commands:
```powershell
$bpEvents = @(
  @{
    host = "appendixg-host"
    service = "market-risk-platform"
    status = "critical"
    description = "Appendix G BigPanda demo event"
    tags = @("appendixg", "market-risk", "demo")
  }
)

$bpEventResponse = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/v1/integrations/bigpanda/events" -Body ($bpEvents | ConvertTo-Json -Depth 10) -ContentType "application/json"
$bpEventResponse | ConvertTo-Json -Depth 10

$bpCorrPayload = @{
  alert_id = "sim-1"
  correlation_ids = @("corr-appendixg-001", "corr-appendixg-002")
}

$bpCorrResponse = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/v1/integrations/bigpanda/correlate" -Body ($bpCorrPayload | ConvertTo-Json -Depth 10) -ContentType "application/json"
$bpCorrResponse | ConvertTo-Json -Depth 10
```

What to highlight:
- events response ok=true
- correlate response indicates attach_correlation behavior

### 6) Close with benefits summary

Narration (suggested):
- "This MVP reduces manual operational overhead by about 1,820 hours per year."
- "It reduces analyst chasing effort through structured ingestion, idempotent processing, and integrated outbound updates."
- "It improves risk and audit posture with deterministic handling, config-version visibility, and traceable run logs."

## Suggested recording length

6 to 8 minutes total:
- 1 min repository/config overview
- 1 min health/version
- 1.5 min idempotency ingest
- 1.5 min email threading/wrapper
- 1.5 min BigPanda events/correlation
- 30 sec benefits close

## Upload guidance (OneDrive/SharePoint)

1. Export video as MP4.
2. File name suggestion: MVP_Demo_Appendix_G_ticmymail.mp4
3. Upload to OneDrive or SharePoint.
4. Set viewer permission to your assessor/supervisor.
5. Paste the share link in the report appendix.
