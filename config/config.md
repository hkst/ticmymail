
The config folder in your ticmymail project contains JSON and Markdown files that define various configuration settings, rules, templates, and schemas for the application. These files are typically loaded at runtime by your Python code (e.g., via loader.py) to customize behavior without hardcoding values. They support features like incident ingestion, email notifications, deduplication, and integrations with BigPanda and ServiceNow. Below, I'll explain the folder structure and each file/subfolder, including how it's used in the context of your FastAPI-based incident management API.

Folder Structure Overview
Detailed Explanation of Each File/Folder
app.json (Main Application Configuration)

Contents: Defines core app settings like service name (ticmymail-part2), environment (dev), deduplication backend (memory or ADLS), logging level, and feature toggles (e.g., enabling ServiceNow, BigPanda, or email).
How It's Used: Loaded at app startup (likely in http_app.py or loader.py). Controls global behavior, such as which integrations are active, dedupe storage (e.g., in-memory for dev, Azure Data Lake Storage for prod), and retry attempts. For example, the features object enables/disables modules like email or BigPanda without code changes.

nfr.json (Non-Functional Requirements)

Contents: Specifies performance thresholds (e.g., P95 response times for ingest/email), error rates, retry limits per integration, and SLA uptime targets.
How It's Used: Used for monitoring and alerting in production. Your code (e.g., in services or API routes) can check these values to enforce SLAs or trigger retries. For instance, if email response time exceeds 1000ms (P95), it might log warnings or escalate. This ensures the app meets operational requirements like 99.9% uptime.
dedupe/v1/dedupe.rules.json (Deduplication Rules)

Contents: Defines fields to hash for uniqueness (e.g., message_id, subject), hash algorithm (sha256), time window (1440 minutes/1 day), and conflict resolution policy (first).
How It's Used: Processed by dedupe_engine.py to prevent duplicate incident creation. When ingesting emails/incidents, it hashes specified fields and checks against a cache/store (configured in app.json). If a match is found within the window, it skips processing, reducing noise in ServiceNow/BigPanda.
email/provider.json (Email Provider Settings)

Contents: Configures email sending via SMTP or Microsoft Graph API, including host/port, TLS settings, and credentials (marked as TODO for placeholders).
How It's Used: Loaded by email_publisher.py to establish connections and send emails. Supports switching providers (e.g., SMTP for local dev, Graph for Azure-hosted). Credentials are injected at runtime (e.g., via environment variables) for security.
email/wrapper.md (Email Wrapper Template)

Contents: A Markdown template that wraps email bodies with a footer (e.g., "This message was sent by ticmymail Part‑2 service").
How It's Used: Applied by the email publisher to standardize outgoing emails. The {{ body }} placeholder is replaced with content from templates below, ensuring consistent branding and disclaimers.
email/templates/ (Email Content Templates)

clarification.md: Template for requesting more info on an incident (e.g., "Please provide additional information").
status.md: Likely for status updates (content not shown, but probably placeholders for incident status).
workaround.md: For workaround notifications (content not shown, but for sharing solutions).
How They're Used: Loaded dynamically in email_publisher.py based on event type (e.g., from schema.json's event_type enum like "info_request" or "workaround"). Placeholders (e.g., {{ incident_id }}) are filled with data from ingested incidents, then wrapped with wrapper.md for sending.
integrations/bigpanda.json (BigPanda Integration Config)

Contents: API endpoint, token, timeout, retry policy, and correlation settings for BigPanda alerts.
How It's Used: Consumed by bigpanda_client.py to send alerts to BigPanda. For example, when an incident is ingested, it posts data to the API with retries and correlation enabled to link related events.
integrations/servicenow.json (ServiceNow Integration Config)

Contents: Instance URL, OAuth credentials, field mappings (e.g., map email subject to incident short_description), API paths, and retry settings.
How It's Used: Used by servicenow_client.py to create/update incidents in ServiceNow. Mappings transform incoming email data into ServiceNow fields, and retries handle API failures.
schema/v1/schema.json (JSON Schema for Validation)

Contents: A JSON Schema (draft-07) defining required fields (e.g., message_id, subject) and allowed values (e.g., event_type enum: "new", "reply", etc.).
How It's Used: Applied in API routes (e.g., routes_ingest.py) via Pydantic or jsonschema library to validate incoming incident data. Ensures data integrity before processing—invalid payloads are rejected with errors.
General Usage Notes
Loading Mechanism: These files are likely read via loader.py, which might use Python's json module or a config library to parse them into dictionaries/objects accessible throughout the app.
Environment-Specific: Many have placeholders (e.g., TODO_*) that are overridden by environment variables or secrets in production (e.g., via Azure Key Vault).
Versioning: Subfolders like v1 allow evolving configs without breaking changes.
Integration with Code: Tied to your service layer (e.g., incident_service.py) and adapters for external systems. For example, dedupe rules prevent spam, while templates customize user communications.
Best Practices: In production, these should be externalized (e.g., via ConfigMaps in Kubernetes) for easier updates without redeploying code.
If you need to modify any file or see how a specific one integrates with your code, let me know!

************
```markdown
# Config Files Documentation

This document describes the configuration files in the `config/` folder of the `ticmymail` project. These files define settings, rules, templates, and schemas for the incident ingestion API, supporting features like deduplication, email notifications, and integrations with BigPanda and ServiceNow.

## Folder Structure

```
config/
├── app.json                    # Main application configuration
├── nfr.json                    # Non-functional requirements (performance/SLA settings)
├── dedupe/
│   └── v1/
│       └── dedupe.rules.json   # Deduplication rules
├── email/
│   ├── provider.json           # Email provider settings
│   ├── wrapper.md              # Email wrapper template
│   └── templates/
│       ├── clarification.md    # Template for clarification requests
│       ├── status.md           # Template for status updates
│       └── workaround.md       # Template for workaround notifications
├── integrations/
│   ├── bigpanda.json           # BigPanda integration config
│   └── servicenow.json         # ServiceNow integration config
└── schema/
    └── v1/
        └── schema.json         # JSON schema for data validation
```

## File Descriptions

### app.json (Main Application Configuration)
Defines core app settings loaded at startup.

- `service_name`: Name of the service (e.g., "ticmymail-part2").
- `environment`: Deployment environment (e.g., "dev").
- `dedupe_root`: Path for dedupe state storage.
- `dedupe`: Settings for deduplication (backend: "memory" or ADLS, TTL, reconcile interval).
- `adls_dedupe`: Azure Data Lake Storage config for persistent dedupe (connection string, container, blob path).
- `config_version`: Version of the config schema.
- `log_level`: Logging level (e.g., "INFO").
- `features`: Toggles for integrations (servicenow, bigpanda, email).

**Usage**: Controls global behavior in `src/tmm/config/loader.py` and services like `dedupe_engine.py`.

### nfr.json (Non-Functional Requirements)
Specifies performance and operational thresholds.

- `p95_ingest_ms`: P95 response time for ingestion (200ms).
- `p95_email_ms`: P95 response time for email (1000ms).
- `error_rate_threshold_percent`: Max error rate (1%).
- `retry_limits`: Max retries per integration (servicenow: 3, bigpanda: 3, email: 2).
- `sla`: Uptime target (99.9%).

**Usage**: Used for monitoring in production; checked in API routes or services to enforce SLAs.

### dedupe/v1/dedupe.rules.json (Deduplication Rules)
Configures how duplicates are detected.

- `dedupe_fields`: Fields to hash (message_id, thread_id, subject, body).
- `hash_algorithm`: Hash method (sha256).
- `window_minutes`: Time window for uniqueness (1440 minutes).
- `conflict_policy`: How to handle conflicts ("first").

**Usage**: Processed by `src/tmm/service/dedupe_engine.py` to prevent duplicate incidents.

### email/provider.json (Email Provider Settings)
Configures email sending.

- `type`: Provider type ("smtp" or "graph").
- `smtp`: SMTP settings (host, port, TLS, credentials).
- `graph`: Microsoft Graph API settings (tenant_id, client_id, client_secret).

**Usage**: Loaded by `src/tmm/adapters/email_publisher.py` for sending emails.

### email/wrapper.md (Email Wrapper Template)
Markdown template for email footers.

- Contains placeholders like `{{ body }}` and a standard footer.

**Usage**: Wraps email content from templates in `email_publisher.py`.

### email/templates/ (Email Content Templates)
Markdown templates for different email types.

- `clarification.md`: For requesting more info (e.g., "Please provide additional information").
- `status.md`: For status updates.
- `workaround.md`: For sharing solutions.

**Usage**: Selected based on event_type in `email_publisher.py`; placeholders filled with incident data.

### integrations/bigpanda.json (BigPanda Integration Config)
Settings for BigPanda alerts.

- `api_url`: BigPanda API endpoint.
- `api_token`: Authentication token.
- `timeout_seconds`: Request timeout (30s).
- `time_window_minutes`: Correlation window (60 minutes).
- `retry_policy`: Retries (max_attempts: 3, backoff: 2s).
- `enable_correlation`: Whether to correlate events.

**Usage**: Used by `src/tmm/adapters/bigpanda_client.py` for API calls.

### integrations/servicenow.json (ServiceNow Integration Config)
Settings for ServiceNow incidents.

- `instance_url`: ServiceNow instance URL.
- `client_id`/`client_secret`: OAuth credentials.
- `scope`: OAuth scope.
- `mappings`: Field mappings (e.g., subject -> short_description).
- `api_paths`: Endpoints for incidents, comments, attachments.
- `timeout_seconds`: Request timeout (30s).
- `retry_policy`: Retries (max_attempts: 3, backoff: 2s).

**Usage**: Used by `src/tmm/adapters/servicenow_client.py` for creating/updating incidents.

### schema/v1/schema.json (JSON Schema for Validation)
JSON Schema (draft-07) for validating incident data.

- Defines required fields (schema_version, event_type, message_id, etc.).
- Enums for event_type ("new", "reply", "info_request", etc.).
- Formats for dates.

**Usage**: Applied in `src/tmm/api/routes_ingest.py` to validate incoming payloads.

## General Notes
- **Loading**: Files are read via `src/tmm/config/loader.py` using Python's `json` module.
- **Environment Overrides**: Placeholders (e.g., "TODO_*") are replaced by environment variables or secrets in production.
- **Versioning**: Subfolders like `v1` allow config evolution.
- **Security**: Sensitive values (tokens, secrets) should be externalized to Azure Key Vault in production.

For updates, modify these files and redeploy. Ensure changes align with code in adapters and services.
```