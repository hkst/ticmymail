import json
import os
from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigLoader:
    def __init__(self, root: Path | str | None = None):
        if root is None:
            root = os.getenv("TMM_CONFIG_ROOT", "config")
        self.root = Path(root)
        self._cache: Dict[str, Any] = {}
        self._hot_reload = False

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
