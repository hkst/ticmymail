import json
from pathlib import Path
from typing import Any, Dict


class ConfigLoader:
    def __init__(self, root: Path | str = "/config"):
        self.root = Path(root)

    def load(self, path: str) -> Dict[str, Any]:
        full = self.root / path
        if not full.exists():
            raise FileNotFoundError(f"Config file not found: {full}")
        return json.loads(full.read_text(encoding="utf-8"))

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

    def nfr(self) -> Dict[str, Any]:
        return self.load("nfr.json")
