import os
import importlib
from abc import ABC, abstractmethod
from typing import Optional


class SecretProvider(ABC):
    @abstractmethod
    def get_secret(self, name: str) -> Optional[str]:
        raise NotImplementedError


class EnvSecretProvider(SecretProvider):
    def __init__(self, prefix: str = "TMM_SECRET_"):
        self.prefix = prefix

    @staticmethod
    def _normalize(name: str) -> str:
        return name.strip().replace("-", "_").upper()

    def get_secret(self, name: str) -> Optional[str]:
        if not name:
            return None

        # Allow explicit env var names and normalized prefixed names.
        direct = os.getenv(name)
        if direct:
            return direct

        normalized = self._normalize(name)
        prefixed = os.getenv(f"{self.prefix}{normalized}")
        if prefixed:
            return prefixed

        normalized_direct = os.getenv(normalized)
        if normalized_direct:
            return normalized_direct

        return None


class AzureKeyVaultSecretProvider(SecretProvider):
    def __init__(self, vault_url: str, use_managed_identity: bool = False):
        self.vault_url = (vault_url or "").strip()
        self.use_managed_identity = use_managed_identity
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return self._client

        if not self.vault_url:
            return None

        try:
            azure_identity = importlib.import_module("azure.identity")
            azure_keyvault_secrets = importlib.import_module("azure.keyvault.secrets")
        except Exception as exc:  # pragma: no cover - dependency/runtime guard
            raise RuntimeError("Azure SDK dependencies are not available") from exc

        credential = azure_identity.DefaultAzureCredential(
            exclude_interactive_browser_credential=self.use_managed_identity,
        )
        self._client = azure_keyvault_secrets.SecretClient(vault_url=self.vault_url, credential=credential)
        return self._client

    def get_secret(self, name: str) -> Optional[str]:
        if not name:
            return None

        client = self._ensure_client()
        if client is None:
            return None

        try:
            secret = client.get_secret(name)
            return secret.value
        except Exception:
            return None


class CompositeSecretProvider(SecretProvider):
    def __init__(self, providers: list[SecretProvider]):
        self.providers = providers

    def get_secret(self, name: str) -> Optional[str]:
        for provider in self.providers:
            value = provider.get_secret(name)
            if value not in (None, ""):
                return value
        return None


def build_secret_provider_from_env() -> tuple[SecretProvider, EnvSecretProvider]:
    mode = os.getenv("TMM_SECRETS_PROVIDER", "auto").strip().lower()
    vault_url = os.getenv("TMM_AKV_VAULT_URL", "").strip()
    use_managed_identity = os.getenv("TMM_AKV_USE_MANAGED_IDENTITY", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    env_provider = EnvSecretProvider(prefix=os.getenv("TMM_SECRET_ENV_PREFIX", "TMM_SECRET_"))

    if mode == "env":
        return env_provider, env_provider

    providers: list[SecretProvider] = []

    if mode == "akv":
        providers.append(AzureKeyVaultSecretProvider(vault_url=vault_url, use_managed_identity=use_managed_identity))
        providers.append(env_provider)
        return CompositeSecretProvider(providers), env_provider

    # auto mode: prefer AKV only when vault URL is configured.
    if mode == "auto" and vault_url:
        providers.append(AzureKeyVaultSecretProvider(vault_url=vault_url, use_managed_identity=use_managed_identity))

    providers.append(env_provider)
    if len(providers) == 1:
        return providers[0], env_provider

    return CompositeSecretProvider(providers), env_provider
