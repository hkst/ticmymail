Set-Location "C:\Users\henley\Documents\Dev\mypy\ticmymail"
$base = "http://127.0.0.1:8000"

Write-Host "=== 1) Health and version ===" -ForegroundColor Cyan
Invoke-RestMethod -Method GET -Uri "$base/v1/health" | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method GET -Uri "$base/v1/version" | ConvertTo-Json -Depth 10

Write-Host "=== 2) Idempotent ingest (same key twice) ===" -ForegroundColor Cyan
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
$r1 = Invoke-RestMethod -Method POST -Uri "$base/v1/incidents/ingest" -Headers $headers -Body ($payload | ConvertTo-Json -Depth 10) -ContentType "application/json"
$r2 = Invoke-RestMethod -Method POST -Uri "$base/v1/incidents/ingest" -Headers $headers -Body ($payload | ConvertTo-Json -Depth 10) -ContentType "application/json"
Write-Host "FIRST RESPONSE" -ForegroundColor Yellow
$r1 | ConvertTo-Json -Depth 10
Write-Host "SECOND RESPONSE" -ForegroundColor Yellow
$r2 | ConvertTo-Json -Depth 10

Write-Host "=== 3) Email template + wrapper + threading ===" -ForegroundColor Cyan
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
$emailResponse = Invoke-RestMethod -Method POST -Uri "$base/v1/comm/email" -Body ($emailPayload | ConvertTo-Json -Depth 10) -ContentType "application/json"
$emailResponse | ConvertTo-Json -Depth 10

Write-Host "=== 4) BigPanda events + correlate ===" -ForegroundColor Cyan
$bpEvents = @(
  @{
    host = "appendixg-host"
    service = "market-risk-platform"
    status = "critical"
    description = "Appendix G BigPanda demo event"
    tags = @("appendixg", "market-risk", "demo")
  }
)
$bpEventResponse = Invoke-RestMethod -Method POST -Uri "$base/v1/integrations/bigpanda/events" -Body ($bpEvents | ConvertTo-Json -Depth 10) -ContentType "application/json"
$bpEventResponse | ConvertTo-Json -Depth 10

$bpCorrPayload = @{
  alert_id = "sim-1"
  correlation_ids = @("corr-appendixg-001", "corr-appendixg-002")
}
$bpCorrResponse = Invoke-RestMethod -Method POST -Uri "$base/v1/integrations/bigpanda/correlate" -Body ($bpCorrPayload | ConvertTo-Json -Depth 10) -ContentType "application/json"
$bpCorrResponse | ConvertTo-Json -Depth 10

Write-Host "=== Demo commands complete ===" -ForegroundColor Green
