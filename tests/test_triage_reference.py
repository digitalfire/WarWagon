import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from benchmarks.triage.reference import evidence_decision, run_baseline, score


FIXTURES = Path(__file__).resolve().parents[1] / "benchmarks/triage/fixtures"


class TriageReferenceTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.alerts = FIXTURES / "alerts.json"
        self.labels = FIXTURES / "labels.json"
        self.decisions = self.root / "decisions.json"

    def write_decisions(self, result):
        self.decisions.write_text(json.dumps(result), encoding="utf-8")

    def test_scores_seeded_fixture_and_reports_which_alerts_were_missed(self):
        self.write_decisions(run_baseline(self.alerts))
        result = score(self.alerts, self.decisions, self.labels)
        self.assertEqual(result["counts"], {
            "true_positive": 2, "false_positive": 2,
            "true_negative": 2, "false_negative": 2,
        })
        self.assertEqual(result["precision"], .5)
        self.assertEqual(result["recall"], .5)
        self.assertEqual(result["missed_alert_ids"], ["A3", "A8"])
        self.assertEqual(result["false_alarm_ids"], ["A1", "A5"])

    def test_refuses_changed_input_or_incomplete_decisions(self):
        result = run_baseline(self.alerts)
        self.write_decisions(result)
        changed = self.root / "edited-alerts.json"
        changed.write_bytes(self.alerts.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "exact alert input"):
            score(changed, self.decisions, self.labels)
        result["decisions"].pop()
        self.write_decisions(result)
        with self.assertRaisesRegex(ValueError, "exactly match"):
            score(self.alerts, self.decisions, self.labels)

    def test_undefined_precision_is_null(self):
        result = run_baseline(self.alerts)
        for decision in result["decisions"]:
            decision["escalate"] = False
        self.write_decisions(result)
        metrics = score(self.alerts, self.decisions, self.labels)
        self.assertIsNone(metrics["precision"])
        self.assertEqual(metrics["recall"], 0)


    def test_evidence_can_change_severity_decision_and_cites_sources(self):
        approved = [
            {"id": "change", "kind": "approved_activity", "source": "change-calendar"},
            {"id": "owner", "kind": "approved_activity", "source": "service-owner"},
        ]
        decision = evidence_decision({"id": "calibration", "severity": "high", "evidence": approved})
        self.assertEqual(decision, {
            "escalate": False, "reason": "corroborated_approved_activity",
            "evidence_ids": ["change", "owner"],
        })

    def test_same_source_never_counts_twice_and_conflict_escalates(self):
        activity = [
            {"id": "login", "kind": "unexpected_activity", "source": "audit"},
            {"id": "copy", "kind": "unexpected_activity", "source": " AUDIT "},
        ]
        alert = {"id": "calibration", "severity": "low", "evidence": activity}
        self.assertEqual(evidence_decision(alert)["reason"], "severity_fallback")
        alert["evidence"] = [
            activity[0], {"id": "change", "kind": "approved_activity", "source": "calendar"},
        ]
        self.assertEqual(evidence_decision(alert), {
            "escalate": True, "reason": "conflicting_evidence", "evidence_ids": ["login", "change"],
        })

    def test_malformed_evidence_is_rejected(self):
        for evidence in ([{"id": "value", "kind": "unconfirmed_signal", "source": ""}], None):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                evidence_decision({"id": "calibration", "severity": "medium", "evidence": evidence})
