Excellent. Use this as your second Copilot Agent prompt for Azure Key Vault infrastructure + app identity wiring.

```text
You are implementing Azure infrastructure and identity wiring for AKV-based secret resolution in this Python service, without changing business behavior.

Objective
Provision and wire Azure resources so the app can resolve secrets at runtime from Azure Key Vault using managed identity, while preserving existing API behavior and config-driven design.

Scope
- Infrastructure + deployment wiring only.
- Do not alter API contracts, payload models, incident routing logic, or adapter business logic.
- Keep existing local-dev path working (env fallback).

Repository context to respect
- Existing app/deployment files should be reused where possible (manifests, config, docs, pyproject).
- Keep current branching and PR flow.
- Add only minimal, targeted changes.

Required outcomes
1) Azure resources ready:
- Resource group (reuse if exists).
- Key Vault with RBAC authorization enabled.
- App hosting target identity wiring (System Assigned Managed Identity preferred).
- Role assignment: Key Vault Secrets User for app identity scoped to vault.
- Optional: App Insights and Log Analytics only if already part of repo pattern.

2) Secret materialization in Key Vault:
- Create secret placeholders (no real secret values in repo):
  - jira-api-token
  - jira-email
  - servicenow-client-secret
  - bigpanda-api-token
- Support secret naming convention in docs.

3) Runtime app configuration wiring:
- Set environment variables expected by app:
  - TMM_SECRETS_PROVIDER=akv
  - TMM_AKV_VAULT_URL=https://<vault-name>.vault.azure.net/
  - TMM_CONFIG_ROOT=<existing config root if needed>
- Keep ability to override with env mode for local dev.

4) Deployment manifest/IaC updates:
- If IaC exists, extend it; do not replace stack.
- If both Bicep and Terraform are absent, choose one (Bicep preferred) and keep it minimal.
- Ensure idempotent deploys.
- Add outputs for vault name, vault URI, principal ID.

5) Security controls:
- No secret values in code, yaml, json, logs, or docs.
- No broad roles like Owner/Contributor for runtime identity.
- Use least privilege role assignment only.

Implementation tasks
A. Discovery and plan first
- Inspect current deployment structure and decide target hosting path (AKS/App Service/Container Apps).
- Produce a short plan with files to edit and why.
- Continue after showing plan.

B. IaC/resource wiring
- Add/modify IaC to provision:
  - Key Vault (RBAC enabled)
  - Managed identity on hosting resource
  - RBAC assignment: Key Vault Secrets User to managed identity
- Add parameters for environment (dev/prod), location, naming prefix.
- Keep defaults safe and non-destructive.

C. App settings wiring
- Update deployment manifests or app config injection so runtime gets:
  - TMM_SECRETS_PROVIDER
  - TMM_AKV_VAULT_URL
- Do not inject actual secret values.

D. Operational scripts/runbook
- Add scripts or documented commands for:
  - az login
  - az account set
  - deploy infra
  - set secrets in AKV (manual secure step)
  - deploy app
  - smoke verify identity can read secrets

E. Documentation
- Add a concise doc:
  - prerequisites
  - identity model
  - how to add/rotate secrets
  - rollback strategy to env provider if AKV unavailable
  - troubleshooting common AKV auth errors (403, DNS, RBAC propagation)

Validation and evidence (must include output summary)
1) Show resolved principalId for app identity.
2) Show role assignment exists for Key Vault Secrets User.
3) Show app env has TMM_SECRETS_PROVIDER and TMM_AKV_VAULT_URL.
4) Run smoke check path that confirms app starts and can attempt secret resolution without exposing values.
5) Run tests relevant to config/startup path and summarize pass/fail.

Guardrails
- Do not commit real credentials.
- Do not weaken branch protections.
- Do not bypass GitHub push protection.
- Do not use destructive git commands.

PR deliverables
- Files changed list with purpose per file.
- Infra diff summary.
- Verification evidence summary.
- Manual steps for ops (where humans input secret values).
- Clear rollback steps.

If repository already has an Azure pattern, follow it exactly. If there is no pattern, implement the smallest secure baseline and document assumptions.
```

If you want, I can also give you a third prompt focused only on CI/CD pipeline wiring for AKV-enabled deploys (develop -> main promotion gates).