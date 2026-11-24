"""Validation gate tests use scripted model doubles; no real inference in CI."""
from pathlib import Path
import json
import tempfile
import threading
import unittest

from warwagon.engagement_store import EngagementLedger
from warwagon.validation import audit_run, run_validation, write_report
from warwagon.worker_runtime import run_two_worker_lab
from tests.test_worker_runtime import ScriptedToolModel, BrokenModel


class ValidationGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.ledger = EngagementLedger(self.path / "runs.sqlite")

    def test_scripted_model_cannot_pass_real_model_identity_gate(self):
        barrier = threading.Barrier(2)
        result = run_two_worker_lab(
            lambda: ScriptedToolModel(barrier), self.ledger,
            workers=2, max_calls=8, max_tokens=4000, max_seconds=30, max_steps=3
        )
        report = audit_run(self.ledger, result["engagementId"],
                           expected_model="scripted-test-double")
        self.assertFalse(report["passed"])
        self.assertFalse(report["checks"]["model_identity_reported"])
        self.assertTrue(report["checks"]["all_tasks_completed"])
        self.assertTrue(report["checks"]["observation_bound_to_invocation"])
        self.assertTrue(report["checks"]["overlapping_task_claims_observed"])
        self.assertTrue(report["checks"]["overlapping_model_call_windows_observed"])
        self.assertTrue(report["checks"]["call_reservations_within_budget"])
        self.assertEqual(report["budget"]["modelCallsReserved"], 4)
        self.assertEqual(report["budget"]["reportedTokens"], 420)
        self.assertNotIn("body", json.dumps(report))
        self.assertNotIn("<b>WW_MARKER</b>", json.dumps(report))
        self.assertTrue(all(len(item["sha256"]) == 64 for item in report["eventDigests"]))

    def test_wrong_model_identity_must_fail_even_with_tool_evidence(self):
        result = run_two_worker_lab(
            ScriptedToolModel, self.ledger,
            workers=2, max_calls=8, max_tokens=4000, max_seconds=30, max_steps=3
        )
        report = audit_run(self.ledger, result["engagementId"], expected_model="qwen3:8b")
        self.assertFalse(report["checks"]["model_identity_reported"])
        self.assertFalse(report["passed"])

    def test_budget_failure_fails_gate(self):
        result = run_two_worker_lab(
            ScriptedToolModel, self.ledger,
            workers=2, max_calls=1, max_tokens=4000, max_seconds=30, max_steps=3
        )
        report = audit_run(self.ledger, result["engagementId"],
                           expected_model="scripted-test-double")
        self.assertFalse(report["passed"])
        self.assertFalse(report["checks"]["recorded_terminal_success"])
        self.assertFalse(report["checks"]["all_tasks_completed"])
        self.assertEqual(report["budget"]["modelCallsReserved"], 1)

    def test_inference_failure_does_not_claim_complete_usage(self):
        result = run_two_worker_lab(
            BrokenModel, self.ledger,
            workers=2, max_calls=4, max_tokens=4000, max_seconds=30, max_steps=2
        )
        report = audit_run(self.ledger, result["engagementId"],
                           expected_model="broken-test-double")
        self.assertFalse(report["passed"])
        self.assertFalse(report["checks"]["all_reserved_calls_accounted"])
        self.assertFalse(report["budget"]["usageComplete"])

    def test_redacted_report_write_is_create_only(self):
        outfile = self.path / "reports" / "run.json"
        write_report(outfile, {"passed": False, "checks": {"real": False}})
        data = json.loads(outfile.read_text())
        self.assertFalse(data["passed"])
        with self.assertRaises(FileExistsError):
            write_report(outfile, {"passed": True})

    def test_preflight_runner_rejects_scripted_model_before_inference(self):
        with self.assertRaisesRegex(ValueError, "test double"):
            run_validation(
                ScriptedToolModel(), self.path / "runs.sqlite",
                workers=2, model_calls=8, tokens=4000, seconds=20,
                steps=3, http_rps=30, output=self.path / "result.json",
            )
        self.assertEqual(self.ledger.list_engagements(), [])


if __name__ == "__main__":
    unittest.main()
