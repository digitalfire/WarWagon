import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from warwagon.arc_scorecard import build_scorecard, read_checklist


class BenchmarkCaseTests(TestCase):
    def test_checked_in_checklist_matches_frozen_proposal(self):
        case = Path(__file__).resolve().parents[1] / "benchmarks/arc/cases/review-index"
        _, checklist, items = read_checklist(case / "checklist.json")
        raw_proposal = (case / "proposal.md").read_bytes()
        self.assertEqual(checklist["proposal_sha256"], hashlib.sha256(raw_proposal).hexdigest())
        self.assertEqual(checklist["role"], "evaluation-science")
        self.assertTrue(items)


class ScorecardTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.report_path = root / "report.json"
        self.checklist_path = root / "checklist.json"
        self.judgments_path = root / "judgments.json"
        self.role = "evaluation-science"
        self.record = {
            "role": self.role,
            "status": "valid",
            "review": {
                "verdict": "conditional", "strengths": [], "blockers": [],
                "experiments": [], "unknowns": [],
            },
        }
        self.report = {
            "kind": "arc_first_pass_report", "schema_version": 1,
            "proposal_sha256": "a" * 64,
            "attempts_by_role": {self.role: [{"artifact_sha256": "b" * 64, "record": self.record}]},
        }
        self.checklist = {
            "kind": "arc_review_quality_checklist", "schema_version": 1,
            "proposal_sha256": "a" * 64, "role": self.role,
            "items": [
                {"id": "baseline", "criterion": "Identify the missing baseline."},
                {"id": "boundary", "criterion": "Discuss the experiment boundary."},
            ],
        }
        self.judgments = {
            "baseline": {"outcome": "not_met", "rationale": "The review proposes no baseline."},
            "boundary": {"outcome": "inconclusive", "rationale": "The proposal omits relevant scope."},
        }

    def score(self, *, report_digest=None):
        for path, data in (
            (self.report_path, self.report),
            (self.checklist_path, self.checklist),
        ):
            path.write_text(json.dumps(data), encoding="utf-8")
        self.judgments_path.write_text(json.dumps({
            "report_sha256": report_digest or hashlib.sha256(self.report_path.read_bytes()).hexdigest(),
            "checklist_sha256": hashlib.sha256(self.checklist_path.read_bytes()).hexdigest(),
            "judgments": self.judgments,
        }), encoding="utf-8")
        return build_scorecard(self.report_path, self.checklist_path, self.judgments_path, "test assessor")

    def test_links_review_checklist_and_judgments_and_preserves_uncertainty(self):
        result = self.score()
        self.assertEqual(result["review_artifact_sha256"], "b" * 64)
        for field, path in (
            ("report_sha256", self.report_path),
            ("checklist_sha256", self.checklist_path),
            ("judgments_sha256", self.judgments_path),
        ):
            self.assertEqual(result[field], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(result["outcome_counts"], {"met": 0, "not_met": 1, "inconclusive": 1})
        self.assertEqual(result["items"][1]["rationale"], self.judgments["boundary"]["rationale"])

    def test_rejects_mismatched_proposal_and_unresolved_review(self):
        self.report["proposal_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "checklist proposal"):
            self.score()
        self.report["proposal_sha256"] = "a" * 64
        self.record["status"] = "invalid_response"
        with self.assertRaisesRegex(ValueError, "no current valid ARC review"):
            self.score()

    def test_rejects_incomplete_judgments_and_duplicate_ids(self):
        del self.judgments["boundary"]
        with self.assertRaisesRegex(ValueError, "exactly the checklist"):
            self.score()
        self.checklist["items"].append(self.checklist["items"][0])
        with self.assertRaisesRegex(ValueError, "duplicate checklist item"):
            self.score()

    def test_rejects_judgments_for_different_report_bytes(self):
        with self.assertRaisesRegex(ValueError, "exact ARC report"):
            self.score(report_digest="c" * 64)
