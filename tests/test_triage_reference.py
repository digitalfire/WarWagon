import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from benchmarks.triage.reference import evidence_decision, guarded_evidence_decision, run_baseline, run_guarded_candidate, score


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


    def test_critical_severity_cannot_be_deferred_by_evidence(self):
        alert = {"id": "critical-safeguard", "severity": "critical", "evidence": [
            {"id": "change", "kind": "approved_activity", "source": "calendar"},
            {"id": "owner", "kind": "approved_activity", "source": "owner"},
        ]}
        self.assertFalse(evidence_decision(alert)["escalate"])
        self.assertEqual(guarded_evidence_decision(alert), {
            "escalate": True, "reason": "critical_severity_guard", "evidence_ids": [],
        })

    def test_only_fresh_in_scope_evidence_can_override_severity(self):
        alert = {
            "id": "filter", "severity": "high", "scope": "report-service",
            "observed_at": "2026-11-23T12:00:00Z",
        }
        evidence = {"kind": "approved_activity", "scope": "report-service",
                    "recorded_at": "2026-11-22T12:00:00Z"}
        alert["evidence"] = [
            {**evidence, "id": "boundary", "source": "calendar"},
            {**evidence, "id": "stale", "source": "history", "recorded_at": "2026-11-22T11:59:59Z"},
            {**evidence, "id": "outside", "source": "other-owner", "scope": "other-service"},
            {**evidence, "id": "future", "source": "future", "recorded_at": "2026-11-23T12:00:01Z"},
            {**evidence, "id": "naive", "source": "clock", "recorded_at": "2026-11-23T11:00:00"},
        ]
        result = guarded_evidence_decision(alert)
        self.assertTrue(result["escalate"])
        self.assertEqual(result["reason"], "severity_fallback")
        self.assertEqual(result["excluded_evidence"], [
            {"id": "stale", "reason": "stale_evidence"},
            {"id": "outside", "reason": "scope_mismatch"},
            {"id": "future", "reason": "future_evidence"},
            {"id": "naive", "reason": "invalid_evidence_timestamp"},
        ])
        alert["evidence"].append(
            {**evidence, "id": "owner", "source": "owner", "recorded_at": "2026-11-23T06:00:00-05:00"},
        )
        result = guarded_evidence_decision(alert)
        self.assertFalse(result["escalate"])
        self.assertEqual(result["evidence_ids"], ["boundary", "owner"])


    def test_guarded_strategy_has_no_critical_misses_on_fresh_holdout(self):
        holdout = FIXTURES.parent / "guarded-held-out"
        alerts = holdout / "alerts.json"
        labels = holdout / "labels.json"
        run = run_guarded_candidate(alerts)
        self.write_decisions(run)
        result = score(alerts, self.decisions, labels)
        self.assertEqual(result["missed_critical_alert_ids"], [])
        critical_ids = {
            alert["id"]
            for alert in json.loads(alerts.read_bytes())["alerts"]
            if alert["severity"] == "critical"
        }
        self.assertTrue(critical_ids)
        self.assertTrue(all(
            decision["escalate"]
            for decision in run["decisions"]
            if decision["id"] in critical_ids
        ))
