import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from tmm.logger import get_run_log_path
from tmm.service.payload_factory import PayloadScenarioFactory


class Phase1BatchRunner:
    def __init__(self, app, sample_payload: Dict[str, Any], output_dir: str | Path = "artifacts/phase1"):
        self.client = TestClient(app, raise_server_exceptions=False)
        self.factory = PayloadScenarioFactory(sample_payload)
        self.output_dir = Path(output_dir)

    def _write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _ingest(self, payload: Dict[str, Any], idem_key: str) -> Dict[str, Any]:
        response = self.client.post(
            "/v1/incidents/ingest",
            json=payload,
            headers={"Idempotency-Key": idem_key, "X-Correlation-Id": idem_key},
        )
        return {
            "status_code": response.status_code,
            "body": response.json(),
        }

    def run(self) -> Dict[str, Any]:
        variations = self.factory.build_variations(30)
        duplicates = self.factory.build_duplicate_demo()

        variation_results: List[Dict[str, Any]] = []
        duplicate_results: List[Dict[str, Any]] = []

        for index, payload in enumerate(variations, start=1):
            variation_results.append(
                {
                    "index": index,
                    "subject": payload["value"][0]["subject"],
                    "result": self._ingest(payload, f"phase1-jira-{index:02d}"),
                }
            )

        for index, payload in enumerate(duplicates, start=1):
            duplicate_results.append(
                {
                    "index": index,
                    "subject": payload["value"][0]["subject"],
                    "result": self._ingest(payload, f"phase1-dedupe-{index:02d}"),
                }
            )

        summary = {
            "payload_count": len(variation_results),
            "dedupe_demo_count": len(duplicate_results),
            "accepted": sum(1 for item in variation_results if item["result"]["body"].get("status") == "accepted"),
            "duplicates": sum(1 for item in duplicate_results if item["result"]["body"].get("status") == "duplicate"),
            "log_file": get_run_log_path(),
        }

        self._write_json(self.output_dir / "jira_payload_variations.json", variations)
        self._write_json(self.output_dir / "jira_payload_dedupe_demo.json", duplicates)
        self._write_json(
            self.output_dir / "phase1_run_summary.json",
            {
                "summary": summary,
                "variation_results": variation_results,
                "duplicate_results": duplicate_results,
            },
        )
        return summary