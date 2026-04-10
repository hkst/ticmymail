import json
import os
from pathlib import Path
from typing import Any, Dict

import yaml
from tmm.config.secret_provider import SecretProvider, build_secret_provider_from_env


class ConfigResolutionError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 500):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class ConfigLoader:
    def __init__(self, root: Path | str | None = None, secret_provider: SecretProvider | None = None):
        if root is None:
            root = os.getenv("TMM_CONFIG_ROOT", "config")
        self.root = Path(root)
        self._cache: Dict[str, Any] = {}
        self._hot_reload = False
        default_provider, env_provider = build_secret_provider_from_env()
        self._secret_provider = secret_provider or default_provider
        self._env_provider = env_provider

    def _resolve_secret_value(self, ref: Dict[str, Any], source_path: str) -> str | None:
        name = str(ref.get("name") or "").strip()
        if not name:
            raise ConfigResolutionError("SECRET_REFERENCE_INVALID", f"Invalid secret_ref in config path '{source_path}'", status_code=500)

        required = bool(ref.get("required", True))
        provider = str(ref.get("provider") or "auto").strip().lower()
        default = ref.get("default")

        if provider == "env":
            value = self._env_provider.get_secret(ref.get("env") or name)
        else:
            value = self._secret_provider.get_secret(name)

        if value in (None, "") and default is not None:
            value = str(default)

        if value in (None, "") and required:
            raise ConfigResolutionError(
                "SECRET_RESOLUTION_FAILED",
                f"Required secret could not be resolved for '{name}' in '{source_path}'",
                status_code=500,
            )
        return value

    def _resolve_secrets_recursive(self, node: Any, source_path: str) -> Any:
        if isinstance(node, dict):
            if "secret_ref" in node and isinstance(node["secret_ref"], dict):
                return self._resolve_secret_value(node["secret_ref"], source_path)
            return {k: self._resolve_secrets_recursive(v, source_path) for k, v in node.items()}

        if isinstance(node, list):
            return [self._resolve_secrets_recursive(item, source_path) for item in node]

        if isinstance(node, str):
            text = node.strip()
            if text.startswith("akv://"):
                name = text[len("akv://") :].strip()
                return self._resolve_secret_value({"provider": "akv", "name": name, "required": True}, source_path)
            if text.startswith("env://"):
                name = text[len("env://") :].strip()
                return self._resolve_secret_value({"provider": "env", "name": name, "required": True}, source_path)

        return node

    def enable_hot_reload(self, enabled: bool = True) -> None:
        self._hot_reload = enabled

    def reload(self) -> None:
        self._cache.clear()

    def _load_file(self, full_path: Path) -> Dict[str, Any]:
        if not full_path.exists():
            raise FileNotFoundError(f"Config file not found: {full_path}")

        ext = full_path.suffix.lower()
        text = full_path.read_text(encoding="utf-8")

        if ext in [".json"]:
            return json.loads(text)
        if ext in [".yaml", ".yml"]:
            return yaml.safe_load(text)

        raise ValueError(f"Unsupported config file format: {ext}")

    def load(self, path: str) -> Dict[str, Any]:
        if path in self._cache and not self._hot_reload:
            return self._cache[path]

        full = self.root / path
        loaded = self._load_file(full)
        loaded = self._resolve_secrets_recursive(loaded, path)

        if not self._hot_reload:
            self._cache[path] = loaded

        return loaded

    def app(self) -> Dict[str, Any]:
        return self.load("app.json")

    def schema(self, version: str = "v1") -> Dict[str, Any]:
        return self.load(f"schema/{version}/schema.json")

    def dedupe(self, version: str = "v1") -> Dict[str, Any]:
        return self.load(f"dedupe/{version}/dedupe.rules.json")

    def servicenow(self) -> Dict[str, Any]:
        return self.load("integrations/servicenow.json")

    def bigpanda(self) -> Dict[str, Any]:
        return self.load("integrations/bigpanda.json")

    def jira(self) -> Dict[str, Any]:
        return self.load("integrations/jira.json")

    def email(self) -> Dict[str, Any]:
        return self.load("email/provider.json")

    def email_wrapper(self) -> str:
        path = self.root / "email" / "wrapper.md"
        if not path.exists():
            raise FileNotFoundError(f"Email wrapper not found: {path}")
        return path.read_text(encoding="utf-8")

    def email_template(self, key: str) -> str:
        path = self.root / "email" / "templates" / f"{key}.md"
        if not path.exists():
            raise FileNotFoundError(f"Email template not found: {path}")
        return path.read_text(encoding="utf-8")

    def nfr(self) -> Dict[str, Any]:
        return self.load("nfr.json")
