# Azure Key Vault Secrets Runbook

## Purpose
Use Azure Key Vault (AKV) for runtime secret resolution without storing real credentials in repository files.

## Environment Variables
- `TMM_SECRETS_PROVIDER`: `akv`, `env`, or `auto`
- `TMM_AKV_VAULT_URL`: AKV URI, for example `https://my-vault.vault.azure.net/`
- `TMM_AKV_USE_MANAGED_IDENTITY`: `true` for managed identity-first auth in Azure
- `TMM_CONFIG_ROOT`: optional config root override, unchanged from current behavior

## Local Development (No Azure Required)
1. Set `TMM_SECRETS_PROVIDER=env`
2. Set secret values as environment variables.
3. Run the service as usual.

Example PowerShell:
```powershell
$env:TMM_SECRETS_PROVIDER = "env"
$env:JIRA_API_TOKEN = "dummy_api_token"
$env:JIRA_EMAIL = "dummy_email"
```

## Azure Deployment with Managed Identity
1. Enable system-assigned managed identity on the app host.
2. Assign `Key Vault Secrets User` role to the app identity on the vault scope.
3. Set app settings:
   - `TMM_SECRETS_PROVIDER=akv`
   - `TMM_AKV_VAULT_URL=https://<vault-name>.vault.azure.net/`
   - `TMM_AKV_USE_MANAGED_IDENTITY=true`

## Secret Naming Convention
Use lowercase kebab-case secret names to match config references:
- `jira-api-token`
- `jira-email`
- `servicenow-client-secret`
- `bigpanda-api-token`

## Rotation Process
1. Create a new value version in AKV for the same secret name.
2. Validate app behavior in non-prod.
3. Promote change by normal deployment pipeline.
4. No code or config file changes are required when name remains unchanged.

## Troubleshooting
- HTTP 403 from Key Vault: verify role assignment and allow time for RBAC propagation.
- Secret not found: verify exact secret name and vault URL.
- Local resolution fails: set `TMM_SECRETS_PROVIDER=env` and provide env vars.

## Rollback
1. Set `TMM_SECRETS_PROVIDER=env`.
2. Provide required values through environment variables.
3. Redeploy or restart service.
