from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from warwagon.arc_compare import compare_scorecards, main
from warwagon.arc_scorecard import build_scorecard


class ComparisonTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.checklist = self.root / "checklist.json"
        self.left_path = self.root / "left.json"
        self.right_path = self.root / "right.json"
        self.write(self.checklist, {
            "kind": "arc_review_quality_checklist",
            "schema_version": 1,
            "proposal_sha256": "a" * 64,
            "role": "evaluation-science",
            "items": [
                {"id": "baseline", "criterion": "Identify the proposed baseline."},
                {"id": "scope", "criterion": "Identify the experiment scope."},
            ],
        })
        self.left = self.build_card("left", "b", "met")
        self.right = self.build_card("right", "c", "not_met")

    @staticmethod
    def write(path, value):
        path.write_bytes(json.dumps(value).encode("utf-8") + b"\r\n")

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def build_card(self, side, review_digest, outcome):
        report = self.root / f"{side}-report.json"
        judgments = self.root / f"{side}-judgments.json"
        self.write(report, {
            "kind": "arc_first_pass_report",
            "schema_version": 1,
            "proposal_sha256": "a" * 64,
            "attempts_by_role": {"evaluation-science": [{
                "artifact_sha256": review_digest * 64,
                "record": {
                    "role": "evaluation-science",
                    "status": "valid",
                    "review": {
                        "verdict": "conditional", "strengths": [], "blockers": [],
                        "experiments": [], "unknowns": [],
                    },
                },
            }]},
        })
        self.write(judgments, {
            "report_sha256": self.digest(report),
            "checklist_sha256": self.digest(self.checklist),
            "judgments": {
                "baseline": {"outcome": outcome, "rationale": f"{side} baseline rationale"},
                "scope": {"outcome": "inconclusive", "rationale": f"{side} scope rationale"},
            },
        })
        return build_scorecard(report, self.checklist, judgments, "test assessor")

    def compare(self):
        self.write(self.left_path, self.left)
        self.write(self.right_path, self.right)
        return compare_scorecards(self.left_path, self.right_path, self.checklist)

    def test_preserves_paired_outcomes_in_checklist_order_and_exact_provenance(self):
        self.right["items"].reverse()
        result = self.compare()
        self.assertEqual(result["checklist_sha256"], self.digest(self.checklist))
        for side, path, scorecard in (
            ("left", self.left_path, self.left), ("right", self.right_path, self.right),
        ):
            self.assertEqual(result[side]["scorecard_sha256"], self.digest(path))
            self.assertEqual(result[side]["judgments_sha256"], scorecard["judgments_sha256"])
            self.assertEqual(result[side]["review_artifact_sha256"], scorecard["review_artifact_sha256"])
        baseline, scope = result["items"]
        self.assertEqual(baseline["id"], "baseline")
        self.assertEqual(baseline["left"], {"outcome": "met", "rationale": "left baseline rationale"})
        self.assertEqual(baseline["right"], {"outcome": "not_met", "rationale": "right baseline rationale"})
        self.assertTrue(baseline["outcomes_differ"])
        self.assertFalse(baseline["has_inconclusive"])
        self.assertEqual(scope["id"], "scope")
        self.assertFalse(scope["outcomes_differ"])
        self.assertTrue(scope["has_inconclusive"])

    def test_rejects_proposal_role_and_checklist_mismatches(self):
        for key, value in (
            ("proposal_sha256", "d" * 64), ("role", "research-skeptic"), ("checklist_sha256", "d" * 64),
        ):
            with self.subTest(field=key), patch.dict(self.right, {key: value}):
                with self.assertRaisesRegex(ValueError, "exact checklist, proposal, and role"):
                    self.compare()

    def test_rejects_duplicate_and_missing_criteria(self):
        self.right["items"].append(self.right["items"][0])
        with self.assertRaisesRegex(ValueError, "duplicate scorecard item"):
            self.compare()
        for card in (self.left, self.right):
            card["items"] = card["items"][:1]
            card["outcome_counts"]["inconclusive"] = 0
        with self.assertRaisesRegex(ValueError, "cover every frozen checklist item"):
            self.compare()

    def test_rejects_changed_criterion_and_invalid_counts(self):
        self.right["items"][0]["criterion"] = "Rewrite the frozen criterion."
        with self.assertRaisesRegex(ValueError, "criterion differs"):
            self.compare()
        self.right["items"][0]["criterion"] = self.left["items"][0]["criterion"]
        for wrong_count in (2, True):
            with self.subTest(count=wrong_count):
                self.right["outcome_counts"]["not_met"] = wrong_count
                with self.assertRaisesRegex(ValueError, "counts do not match"):
                    self.compare()

    def test_rejects_duplicate_scorecard_even_with_different_item_order(self):
        self.right = deepcopy(self.left)
        self.right["items"].reverse()
        with self.assertRaisesRegex(ValueError, "two distinct scorecards"):
            self.compare()

    def test_cli_writes_result_and_preserves_existing_output(self):
        expected = self.compare()
        output = self.root / "comparison.json"
        command = [
            "arc_compare", str(self.left_path), str(self.right_path),
            "--checklist", str(self.checklist), "--output", str(output),
        ]
        with patch("sys.argv", command):
            main()
        original = output.read_bytes()
        self.assertEqual(json.loads(original), expected)
        with patch("sys.argv", command), patch("sys.stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as error:
                main()
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(output.read_bytes(), original)
