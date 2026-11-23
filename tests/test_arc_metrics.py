import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from warwagon.arc import ROLES
from warwagon.arc_metrics import build_metrics


class MetricsTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.report_path = Path(directory.name) / "report.json"
        self.role = next(iter(ROLES))
        self.report = {
            "kind": "arc_first_pass_report",
            "schema_version": 1,
            "proposal_sha256": "a" * 64,
            "first_pass_sha256": "b" * 64,
            "attempts_by_role": {
                role: [self.attempt(role, "valid", "b" * 64)] for role in ROLES
            },
        }

    @staticmethod
    def attempt(role, status, digest, **measurements):
        return {
            "artifact_sha256": digest,
            "record": {"role": role, "status": status, **measurements},
        }

    def metrics(self):
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
        return build_metrics(self.report_path)

    def test_counts_failed_and_retried_attempts_with_partial_measurements(self):
        self.report["attempts_by_role"][self.role] = [
            self.attempt(self.role, "request_failed", "b" * 64, elapsed_seconds=0.125),
            self.attempt(
                self.role, "invalid_response", "c" * 64, elapsed_seconds=0.375,
                usage={"prompt_tokens": 12, "completion_tokens": 0},
            ),
            self.attempt(
                self.role, "valid", "d" * 64, elapsed_seconds=0.5,
                usage={"prompt_tokens": 20, "total_tokens": 25},
            ),
        ]

        result = self.metrics()
        attempt_count = len(ROLES) + 2
        self.assertEqual(result["report_sha256"], hashlib.sha256(self.report_path.read_bytes()).hexdigest())
        self.assertEqual(result["invocation_attempt_count"], attempt_count)
        self.assertEqual(result["retry_attempt_count"], 2)
        self.assertEqual(result["attempts_by_status"], {
            "valid": len(ROLES), "request_failed": 1, "invalid_response": 1,
        })
        self.assertEqual(result["tokens"], {
            "prompt_tokens": {
                "observed_total": 32, "reported_attempt_count": 2,
                "missing_attempt_count": attempt_count - 2,
            },
            "completion_tokens": {
                "observed_total": 0, "reported_attempt_count": 1,
                "missing_attempt_count": attempt_count - 1,
            },
            "total_tokens": {
                "observed_total": 25, "reported_attempt_count": 1,
                "missing_attempt_count": attempt_count - 1,
            },
        })
        self.assertEqual(result["elapsed_seconds"], {
            "observed_total": 1.0, "reported_attempt_count": 3,
            "missing_attempt_count": attempt_count - 3,
        })

    def test_unusable_values_are_missing_without_inferred_totals(self):
        record = self.report["attempts_by_role"][self.role][0]["record"]
        record["usage"] = {"prompt_tokens": True, "completion_tokens": -1, "total_tokens": "4"}
        record["elapsed_seconds"] = float("inf")

        result = self.metrics()
        unknown = {
            "observed_total": None, "reported_attempt_count": 0,
            "missing_attempt_count": len(ROLES),
        }
        self.assertTrue(all(field == unknown for field in result["tokens"].values()))
        self.assertEqual(result["elapsed_seconds"], unknown)

    def test_rejects_wrong_schema_and_mismatched_attempt_role(self):
        self.report["schema_version"] = True
        with self.assertRaisesRegex(ValueError, "expected an ARC v1"):
            self.metrics()

        self.report["schema_version"] = 1
        self.report["attempts_by_role"][self.role][0]["record"]["role"] = "unknown"
        with self.assertRaisesRegex(ValueError, "invalid attempt record"):
            self.metrics()

    def test_rejects_duplicate_attempt(self):
        attempt = self.attempt(self.role, "request_failed", "b" * 64)
        self.report["attempts_by_role"][self.role] = [attempt, attempt]
        with self.assertRaisesRegex(ValueError, "duplicate attempt digest"):
            self.metrics()
