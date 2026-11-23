import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from benchmarks.triage.reference import run_guarded_candidate
from benchmarks.triage.review_queue import build_queue


class ReviewQueueTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.alerts = self.root / "alerts.json"
        self.decisions = self.root / "decisions.json"

    def write_fixture(self):
        def signal(key, recorded_at, scope="service", kind="unexpected_activity"):
            return {"id": key, "kind": kind, "source": "audit", "scope": scope, "recorded_at": recorded_at}

        records = [
            ("L1", "low", signal("fresh", "2026-11-23T10:00:00Z")),
            ("M1", "medium", signal("stale", "2026-11-21T10:00:00Z")),
            ("M2", "medium", signal("wrong-scope", "2026-11-23T10:00:00Z", scope="other")),
            ("L2", "low", signal("future", "2026-11-23T12:01:00Z")),
            ("L3", "low", signal("invalid-clock", "2026-11-23T10:00:00")),
            ("L4", "low", signal("approval", "2026-11-23T10:00:00Z", kind="approved_activity")),
            ("C1", "critical", signal("escalated", "2026-11-23T10:00:00Z")),
        ]
        self.alerts.write_text(json.dumps({
            "kind": "triage_alerts", "schema_version": 1,
            "alerts": [
                {"id": key, "severity": severity, "observed_at": "2026-11-23T12:00:00Z",
                 "scope": "service", "evidence": [event]}
                for key, severity, event in records
            ],
        }), encoding="utf-8")
        self.decisions.write_text(json.dumps(run_guarded_candidate(self.alerts)), encoding="utf-8")

    def test_prioritizes_unresolved_signals_and_preserves_input_bytes(self):
        self.write_fixture()
        before = self.decisions.read_bytes()
        result = build_queue(self.alerts, self.decisions)
        self.assertEqual([item["id"] for item in result["items"]], ["M1", "L1", "L3"])
        self.assertEqual([item["signals"][0]["reason"] for item in result["items"]], [
            "unexpected_activity_needs_fresh_evidence",
            "unresolved_unexpected_activity",
            "unexpected_activity_needs_timestamp",
        ])
        self.assertEqual(result["decisions_sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(self.decisions.read_bytes(), before)

    def test_rejects_wrong_alert_bytes_and_critical_deferral(self):
        self.write_fixture()
        self.alerts.write_bytes(self.alerts.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "exact alert input"):
            build_queue(self.alerts, self.decisions)
        self.write_fixture()
        run = json.loads(self.decisions.read_bytes())
        run["decisions"][-1]["escalate"] = False
        self.decisions.write_text(json.dumps(run), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "deferred a critical"):
            build_queue(self.alerts, self.decisions)
