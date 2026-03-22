import json
from pathlib import Path
from typing import Any, Dict


class ConfigError(RuntimeError):
    pass


class ConfigManager:
    def __init__(self, config_base: Path | str = "/config"):
        self.base = Path(config_base)

    def _load_json(self, rel_path: str) -> Dict[str, Any]:
        p = self.base / rel_path
        if not p.exists():
            raise ConfigError(f"Missing config: {p}")
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)

    def app(self) -> Dict[str, Any]:
        return self._load_json("app.json")

    def schema(self, version: str = "v1") -> Dict[str, Any]:
        return self._load_json(f"schema/{version}.json")

    def dedupe_config(self, version: str = "v1") -> Dict[str, Any]:
        return self._load_json(f"dedupe/{version}.json")

    def servicenow(self) -> Dict[str, Any]:
        return self._load_json("integrations/servicenow.json")

    def bigpanda(self) -> Dict[str, Any]:
        return self._load_json("integrations/bigpanda.json")

    def email_provider(self) -> Dict[str, Any]:
        return self._load_json("email/provider.json")

    def nfr(self) -> Dict[str, Any]:
        return self._load_json("nfr.json")

    def email_templates(self) -> Dict[str, str]:
        root = self.base / "email/templates"
        if not root.exists():
            raise ConfigError(f"Missing templates directory: {root}")
        out: Dict[str, str] = {}
        for p in root.glob("*.md"):
            out[p.stem] = p.read_text(encoding="utf-8")
        return out

    def email_wrapper(self) -> str:
        p = self.base / "email/wrapper.md"
        if not p.exists():
            raise ConfigError(f"Missing wrapper: {p}")
        return p.read_text(encoding="utf-8")
