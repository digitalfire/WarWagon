import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from benchmarks.planner.score_health import score


class HealthScoreTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        case = self.write("case", services={"alpha": 41001, "beta": 41002})
        self.case_hash = self.digest(case)
        self.write("labels", case_sha256=self.case_hash, status_by_service={"alpha": 204, "beta": 503})

    def write(self, kind, **values):
        path = self.root / f"{kind}.json"
        path.write_text(
            json.dumps({"kind": f"planner_health_{kind}", "schema_version": 1, **values}),
            encoding="utf-8",
        )
        return path

    def digest(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def observation(self, port, status, **changes):
        return {
            "kind": "local_http_connectivity_trace",
            "schema_version": 1,
            "method": "HEAD",
            "url": f"http://127.0.0.1:{port}/",
            "remote_ip": "127.0.0.1",
            "remote_port": port,
            "status_code": status,
            "redirects_followed": 0,
            "error_type": None,
            **changes,
        }

    def evaluate(self, observations, claims, *, change_evidence=False):
        evidence = self.write("evidence", case_sha256=self.case_hash, observations=observations)
        submission = self.write(
            "submission", case_sha256=self.case_hash, evidence_sha256=self.digest(evidence), claims=claims
        )
        if change_evidence:
            evidence.write_bytes(evidence.read_bytes() + b"\n")
        return score(self.root / "case.json", evidence, submission, self.root / "labels.json")

    def test_correct_labels_require_the_matching_service_trace(self):
        result = self.evaluate(
            [self.observation(41001, 204), self.observation(41002, 503)],
            {
                "alpha": {"status_code": 204, "observation_index": 0},
                "beta": {"status_code": 503, "observation_index": 0},
                "gamma": {"status_code": 204, "observation_index": 0},
            },
        )
        self.assertEqual(result["services"], {
            "alpha": "verified", "beta": "invalid_observation", "gamma": "unexpected_service"
        })
        self.assertEqual(result["precision"], 1 / 3)
        self.assertEqual(result["recall"], 1 / 2)

    def test_unsupported_and_missing_claims(self):
        result = self.evaluate(
            [self.observation(41001, 204)],
            {"alpha": {"status_code": 200, "observation_index": 0}},
        )
        self.assertEqual(result["services"], {"alpha": "unsupported_claim", "beta": "missing_claim"})

    def test_redirect_and_missing_observation_receive_no_credit(self):
        result = self.evaluate(
            [self.observation(41001, 204, redirects_followed=1)],
            {
                "alpha": {"status_code": 204, "observation_index": 0},
                "beta": {"status_code": 503, "observation_index": -1},
            },
        )
        self.assertEqual(result["services"], {
            "alpha": "invalid_observation", "beta": "missing_observation"
        })

    def test_fixture_mismatch_invalidates_metrics(self):
        result = self.evaluate(
            [self.observation(41001, 200)],
            {},
        )
        self.assertFalse(result["scorable"])
        self.assertEqual(result["services"]["alpha"], "fixture_mismatch")
        self.assertIsNone(result["precision"])
        self.assertIsNone(result["recall"])

    def test_submission_must_match_exact_evidence_bytes(self):
        with self.assertRaisesRegex(ValueError, "evidence digest mismatch"):
            self.evaluate([], {}, change_evidence=True)

    def test_labels_must_match_exact_case_bytes(self):
        self.write("labels", case_sha256="0" * 64, status_by_service={"alpha": 204, "beta": 503})
        with self.assertRaisesRegex(ValueError, "case digest mismatch"):
            self.evaluate([], {})
