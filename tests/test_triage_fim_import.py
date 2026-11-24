"""Offline importer coverage using synthetic, vendor-shaped Wazuh records."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from benchmarks.triage.fim_import import import_alerts
from benchmarks.triage.reference import run_guarded_candidate


def _jsonl(record, ending=b"\n"):
    return json.dumps(record).encode("utf-8") + ending


def _synthetic_file_change():
    return {
        "timestamp": "2026-11-23T18:17:18.123+0200",
        "rule": {
            "id": "550",
            "description": "Integrity checksum changed.",
            "groups": ["ossec", "syscheck", "syscheck_entry_modified", "syscheck_file"],
            "level": 7,
        },
        "agent": {"id": "010", "name": "synthetic-host"},
        "manager": {"name": "synthetic-manager"},
        "id": "1234567890.00001",
        "full_log": "unselected record data",
        "syscheck": {"path": "/example/docs/settings.txt", "event": "modified"},
    }


class FimImportTests(unittest.TestCase):
    def setUp(self):
        workspace = TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.source = Path(workspace.name) / "alerts.json"
        self.output = Path(workspace.name) / "triage.json"

    def run_cli(self):
        return subprocess.run(
            [sys.executable, "-m", "benchmarks.triage.fim_import",
             str(self.source), "--output", str(self.output)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_cli_preserves_exact_provenance_and_runs_existing_guarded_strategy(self):
        record = _synthetic_file_change()
        unrelated = _jsonl({"rule": {"id": "600", "groups": ["authentication"]}})
        monitor_health = _jsonl({"rule": {"id": "230", "groups": ["syscheck", "fim_db_state"]}})
        first_raw = _jsonl(record, b"\r\n")
        critical = {**record, "rule": {**record["rule"], "level": 15}}
        critical_raw = _jsonl(critical, b"")
        raw = unrelated + monitor_health + b"\n" + first_raw * 2 + critical_raw
        self.source.write_bytes(raw)

        result = self.run_cli()

        self.assertEqual(result.returncode, 0, result.stderr)
        artifact = json.loads(self.output.read_bytes())
        self.assertEqual(artifact, import_alerts(self.source))
        self.assertEqual(self.source.read_bytes(), raw)
        self.assertEqual(artifact["source"], {
            "kind": "wazuh-alerts-jsonl", "sha256": hashlib.sha256(raw).hexdigest(),
        })
        alert, duplicate, critical_alert = artifact["alerts"]
        self.assertEqual(alert["source"], {
            "line": 4, "record_sha256": hashlib.sha256(first_raw).hexdigest(),
        })
        self.assertEqual(duplicate["source"]["record_sha256"], alert["source"]["record_sha256"])
        self.assertNotEqual(duplicate["id"], alert["id"])
        self.assertEqual(critical_alert["source"], {
            "line": 6, "record_sha256": hashlib.sha256(critical_raw).hexdigest(),
        })
        self.assertEqual(alert["observed_at"], "2026-11-23T16:17:18.123000Z")
        self.assertEqual(alert["severity"], "medium")
        self.assertEqual(alert["scope"], 'wazuh-fim:["synthetic-manager","010","/example/docs/settings.txt"]')
        self.assertEqual(alert["wazuh"], {
            "path": "/example/docs/settings.txt", "event": "modified", "agent_id": "010",
            "manager_name": "synthetic-manager", "rule_id": "550", "rule_level": 7,
        })
        self.assertEqual(alert["evidence"], [])
        self.assertNotIn("labels", artifact)
        self.assertNotIn("unselected record data", self.output.read_text())
        decisions = run_guarded_candidate(self.output)["decisions"]
        self.assertEqual([entry["reason"] for entry in decisions], [
            "severity_fallback", "severity_fallback", "critical_severity_guard",
        ])
        self.assertEqual([entry["escalate"] for entry in decisions], [False, False, True])

    def test_missing_context_is_preserved(self):
        self.source.write_bytes(_jsonl({
            "rule": {"id": "554", "level": 4},
            "agent": {"id": "010"},
            "syscheck": {"path": "/example/fixture.txt"},
        }))
        alert, = import_alerts(self.source)["alerts"]
        self.assertEqual(alert["severity"], "low")
        self.assertEqual(alert["summary"], "Wazuh file-integrity event [/example/fixture.txt]")
        self.assertNotIn("observed_at", alert)
        self.assertNotIn("scope", alert)
        self.assertNotIn("event", alert["wazuh"])
        self.assertNotIn("manager_name", alert["wazuh"])

    def test_malformed_records_fail_before_creating_output(self):
        record = _synthetic_file_change()
        malformed = (
            (b'{"rule":\n', "source line 2"),
            (b'{"syscheck":{},"syscheck":{}}\n', "duplicate JSON key"),
            (_jsonl({**record, "syscheck": None}), "syscheck must be an object"),
            (_jsonl({**record, "syscheck": {"path": " "}}), "syscheck.path"),
            (_jsonl({"rule": record["rule"]}), "syscheck must be an object"),
            (_jsonl({**record, "rule": {**record["rule"], "level": True}}), "rule.level"),
            (_jsonl({**record, "rule": {**record["rule"], "level": 17}}), "rule.level"),
            (_jsonl({**record, "rule": {**record["rule"], "id": 550}}), "rule.id"),
            (_jsonl({**record, "timestamp": "2026-11-23T18:17:18"}), "timestamp"),
            (_jsonl({**record, "timestamp": "0001-01-01T00:00:00+01:00"}), "timestamp"),
        )
        for bad_line, message in malformed:
            with self.subTest(message=message, bad_line=bad_line):
                self.source.write_bytes(_jsonl(record) + bad_line)
                with self.assertRaisesRegex(ValueError, message):
                    import_alerts(self.source)
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("source line 2", result.stderr)
        self.assertFalse(self.output.exists())

    def test_empty_selection_fails_and_existing_output_is_preserved(self):
        self.source.write_bytes(_jsonl({"rule": {"id": "600"}}))
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("no Wazuh file-integrity alerts", result.stderr)
        self.assertFalse(self.output.exists())

        self.source.write_bytes(_jsonl(_synthetic_file_change()))
        self.output.write_bytes(b"existing output")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.output.read_bytes(), b"existing output")


if __name__ == "__main__":
    unittest.main()
