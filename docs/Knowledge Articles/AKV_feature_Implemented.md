Implemented. Azure Key Vault secret resolution is now integrated with your existing config-driven pattern while preserving adapter and API behavior.

What was delivered

New secret provider abstraction and implementations
secret_provider.py
Includes:
SecretProvider interface
EnvSecretProvider
AzureKeyVaultSecretProvider using DefaultAzureCredential and SecretClient via dynamic import
CompositeSecretProvider with AKV then env fallback
Environment-driven provider builder using:
TMM_SECRETS_PROVIDER
TMM_AKV_VAULT_URL
TMM_AKV_USE_MANAGED_IDENTITY
ConfigLoader recursive secret resolution
loader.py
Added:
Recursive resolution for object format secret_ref
Short forms: akv://name and env://name
Required secret enforcement with safe error type (no secret value leakage)
Local ConfigResolutionError to avoid circular import
Preserved:
Cache behavior
Hot reload behavior
Existing loader method signatures and usage patterns
Config package exports updated
__init__.py
Integration config templates migrated to secret_ref pattern
jira.json
servicenow.json
bigpanda.json
Uses AKV references with safe non-secret defaults for backward compatibility.
Tests added and updated
New targeted tests:
test_secret_resolution.py
Existing contract fixture updated to use secret_ref:
test_contracts.py
Dependency update
pyproject.toml
Added azure-identity and azure-keyvault-secrets.
Runbook documentation
AKV_Secrets_Runbook.md
Covers local env mode, AKV managed identity setup expectations, naming, rotation, troubleshooting, rollback.
Validation summary

Secret resolution unit tests
Command run: pytest test_secret_resolution.py -q
Result: 6 passed
Existing contract tests
Command run: pytest test_contracts.py -q
Result: 14 passed
Local env-based smoke
ConfigLoader jira load with env mode and env vars
Output showed resolved values present:
provider env
api_token resolved
email resolved
Mocked AKV path proof
Added explicit mocked AKV mode test in test_secret_resolution.py
Confirms AKV provider path resolves secret_ref when TMM_SECRETS_PROVIDER is akv and vault URL is set.
Migration notes

Existing adapters remain unchanged and still receive fully resolved config dictionaries.
No API route or payload contract changes.
Local development remains functional via env mode and fallback defaults in config templates.
Secret resolution now occurs centrally in ConfigLoader, preserving design pattern boundaries.
Rollback plan

Set TMM_SECRETS_PROVIDER to env.
Provide required secret values via environment variables.
Keep current secret_ref config entries (they continue to work with env mode).
If needed, revert only:
loader.py
secret_provider.py
integration config template files
test additions
PR checklist for your description

Revoke and rotate previously exposed Jira token.
Set new token and related values in Key Vault.
Grant app identity Key Vault Secrets User role.
Remove any plaintext secrets from configs and environment history.
Verify Jira ingest path still returns expected behavior in dry_run and non-dry_run modes.
One environment note: installing Azure SDK in your current local ARM venv failed due upstream cryptography wheel/toolchain constraints, but runtime/tests still pass because AKV imports are optional and dynamically loaded. On deployment targets using standard x64 Linux containers or Azure host images, those dependencies should install normally.