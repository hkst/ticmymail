import json

import pytest

from tmm.config.loader import ConfigLoader, ConfigResolutionError
from tmm.config.secret_provider import AzureKeyVaultSecretProvider, SecretProvider


class StubSecretProvider(SecretProvider):
    def __init__(self, secrets: dict[str, str] | None = None):
        self.secrets = secrets or {}

    def get_secret(self, name: str):
        return self.secrets.get(name)


@pytest.fixture
def temp_config_root(tmp_path):
    root = tmp_path / "config"
    (root / "integrations").mkdir(parents=True, exist_ok=True)
    return root


def test_secret_ref_resolves_via_provider(temp_config_root):
    cfg = {
        "base_url": "https://example.atlassian.net",
        "api_token": {"secret_ref": {"provider": "akv", "name": "jira-api-token", "required": True}},
        "email": "tester@example.com",
    }
    (temp_config_root / "integrations" / "jira.json").write_text(json.dumps(cfg), encoding="utf-8")

    loader = ConfigLoader(root=str(temp_config_root), secret_provider=StubSecretProvider({"jira-api-token": "token123"}))
    jira = loader.jira()

    assert jira["api_token"] == "token123"
    assert jira["email"] == "tester@example.com"


def test_env_fallback_resolves_short_env_ref(temp_config_root, monkeypatch):
    cfg = {
        "api_token": "env://JIRA_API_TOKEN"
    }
    (temp_config_root / "integrations" / "jira.json").write_text(json.dumps(cfg), encoding="utf-8")

    monkeypatch.setenv("JIRA_API_TOKEN", "from-env")
    monkeypatch.setenv("TMM_SECRETS_PROVIDER", "env")

    loader = ConfigLoader(root=str(temp_config_root), secret_provider=StubSecretProvider())
    jira = loader.jira()

    assert jira["api_token"] == "from-env"


def test_required_secret_missing_raises_controlled_error(temp_config_root):
    cfg = {
        "api_token": {"secret_ref": {"provider": "akv", "name": "jira-api-token", "required": True}}
    }
    (temp_config_root / "integrations" / "jira.json").write_text(json.dumps(cfg), encoding="utf-8")

    loader = ConfigLoader(root=str(temp_config_root), secret_provider=StubSecretProvider())

    with pytest.raises(ConfigResolutionError) as exc:
        loader.jira()

    assert exc.value.code == "SECRET_RESOLUTION_FAILED"
    assert "jira-api-token" in exc.value.message
    # Ensure error message does not leak actual secret content.
    assert "ATATT" not in exc.value.message


def test_non_secret_values_untouched(temp_config_root):
    cfg = {
        "enabled": True,
        "service_desk_id": "2",
        "request_field_map": {"dept_name": "customfield_10101"},
    }
    (temp_config_root / "integrations" / "jira.json").write_text(json.dumps(cfg), encoding="utf-8")

    loader = ConfigLoader(root=str(temp_config_root), secret_provider=StubSecretProvider())
    jira = loader.jira()

    assert jira["enabled"] is True
    assert jira["service_desk_id"] == "2"
    assert jira["request_field_map"]["dept_name"] == "customfield_10101"


def test_default_value_used_when_secret_optional(temp_config_root):
    cfg = {
        "api_token": {
            "secret_ref": {
                "provider": "akv",
                "name": "jira-api-token",
                "required": False,
                "default": "dummy_api_token",
            }
        }
    }
    (temp_config_root / "integrations" / "jira.json").write_text(json.dumps(cfg), encoding="utf-8")

    loader = ConfigLoader(root=str(temp_config_root), secret_provider=StubSecretProvider())
    jira = loader.jira()
    assert jira["api_token"] == "dummy_api_token"


def test_akv_mode_with_mocked_provider(temp_config_root, monkeypatch):
    cfg = {
        "api_token": {
            "secret_ref": {
                "provider": "akv",
                "name": "jira-api-token",
                "required": True,
            }
        }
    }
    (temp_config_root / "integrations" / "jira.json").write_text(json.dumps(cfg), encoding="utf-8")

    monkeypatch.setenv("TMM_SECRETS_PROVIDER", "akv")
    monkeypatch.setenv("TMM_AKV_VAULT_URL", "https://unit-test-vault.vault.azure.net/")

    def _mock_get_secret(self, name: str):
        if name == "jira-api-token":
            return "akv-mocked-token"
        return None

    monkeypatch.setattr(AzureKeyVaultSecretProvider, "get_secret", _mock_get_secret)

    loader = ConfigLoader(root=str(temp_config_root))
    jira = loader.jira()
    assert jira["api_token"] == "akv-mocked-token"
