import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from benchmarks.triage.reference import run_guarded_candidate
from benchmarks.triage.recheck import recheck_evidence
from benchmarks.triage.review_queue import build_queue


class RecheckEvidenceTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.alerts = root / "alerts.json"
        self.decisions = root / "decisions.json"
        self.queue = root / "queue.json"
        self.update_path = root / "update.json"
        self.write(self.alerts, {
            "kind": "triage_alerts", "schema_version": 1,
            "alerts": [{
                "id": "A1", "severity": "low", "scope": "service",
                "observed_at": "2026-11-23T12:00:00Z",
                "evidence": [{
                    "id": "old", "kind": "unexpected_activity", "source": "audit",
                    "scope": "service", "recorded_at": "2026-11-21T11:00:00Z",
                }],
            }],
        })
        self.write(self.decisions, run_guarded_candidate(self.alerts))
        self.write(self.queue, build_queue(self.alerts, self.decisions))
        self.update = {
            "kind": "triage_analyst_evidence_update", "schema_version": 1,
            "queue_sha256": self.sha256(self.queue),
            "alert_id": "A1", "evidence_id": "old",
            "observation": {
                "id": "new", "kind": "unexpected_activity", "source": "analyst",
                "scope": "service", "recorded_at": "2026-11-22T07:00:00-05:00",
            },
        }

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    @staticmethod
    def sha256(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def recheck(self):
        self.write(self.update_path, self.update)
        return recheck_evidence(self.alerts, self.decisions, self.queue, self.update_path)

    def test_inclusive_boundary_preserves_provenance_and_existing_deferral(self):
        paths = (self.alerts, self.decisions, self.queue)
        before = [path.read_bytes() for path in paths]
        result = self.recheck()
        self.assertEqual(result, {
            "kind": "triage_analyst_evidence_recheck", "schema_version": 1,
            "alerts_sha256": self.sha256(self.alerts),
            "decisions_sha256": self.sha256(self.decisions),
            "queue_sha256": self.sha256(self.queue),
            "update_sha256": self.sha256(self.update_path),
            "alert_id": "A1", "original_evidence_id": "old",
            "replacement_evidence_id": "new", "status": "eligible", "reason": None,
        })
        self.assertEqual([path.read_bytes() for path in paths], before)
        self.assertFalse(json.loads(before[1])["decisions"][0]["escalate"])

    def test_records_scope_freshness_and_strict_timestamp_failures(self):
        for scope, recorded_at, reason in (
            ("other", "2026-11-23T11:00:00Z", "scope_mismatch"),
            ("service", "2026-11-22T11:59:59.999999Z", "stale_evidence"),
            ("service", "2026-11-23T12:00:00.000001Z", "future_evidence"),
            ("service", "2026-11-23T11:00:00", "invalid_evidence_timestamp"),
            ("service", "2026-11-23 11:00:00+00:00", "invalid_evidence_timestamp"),
            ("service", "2026-11-23T11:00:00+00:60", "invalid_evidence_timestamp"),
            ("service", "2026-11-31T11:00:00Z", "invalid_evidence_timestamp"),
        ):
            with self.subTest(reason=reason, recorded_at=recorded_at):
                self.update["observation"].update(scope=scope, recorded_at=recorded_at)
                result = self.recheck()
                self.assertEqual((result["status"], result["reason"]), ("ineligible", reason))

    def test_rejects_changed_queue_decisions_and_unqueued_evidence(self):
        self.update["evidence_id"] = "unlisted"
        with self.assertRaisesRegex(ValueError, "queued alert and evidence pair"):
            self.recheck()
        self.update["evidence_id"] = "old"
        self.queue.write_bytes(self.queue.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "exact review queue"):
            self.recheck()
        self.update["queue_sha256"] = self.sha256(self.queue)
        self.decisions.write_bytes(self.decisions.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "queue must match"):
            self.recheck()

    def test_rejects_tampered_evidence_reference_even_with_matching_digests(self):
        queue = json.loads(self.queue.read_bytes())
        queue["items"][0]["signals"][0]["evidence_id"] = "invented"
        self.write(self.queue, queue)
        self.update["queue_sha256"] = self.sha256(self.queue)
        self.update["evidence_id"] = "invented"
        with self.assertRaisesRegex(ValueError, "queue must match"):
            self.recheck()
