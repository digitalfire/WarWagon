import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from warwagon.arc_challenge import build_challenge
from warwagon.arc_report import build_report
from test_arc_report import valid
from warwagon.arc import ROLES


class ChallengeTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.role = "distributed-systems"
        self.record = valid(self.role, "conditional")
        self.record["review"]["blockers"] = ["Recovery behavior has no test evidence."]
        self.report = self.root / "report.json"

    def write_report(self):
        first = self.root / "first.json"
        first.write_text(json.dumps({
            "kind": "real_model_first_pass_reviews",
            "schema_version": 1,
            "proposal_sha256": "proposal",
            "reviews": [self.record if role == self.role else valid(role, "support") for role in ROLES],
        }), encoding="utf-8")
        self.report.write_text(json.dumps(build_report(first, [])), encoding="utf-8")
        return hashlib.sha256(first.read_bytes()).hexdigest()

    def challenge(self, challenger="research-skeptic", index=0):
        return build_challenge(
            self.report, self.role, "blockers", index, challenger,
            "The scope of the blocker is unclear.", "List the recovery scenarios and their tests.",
        )

    def test_challenge_links_exact_report_review_and_item(self):
        digest = self.write_report()
        report_bytes = self.report.read_bytes()
        result = self.challenge()
        self.assertEqual(result["status"], "open")
        self.assertEqual(result["report_sha256"], hashlib.sha256(report_bytes).hexdigest())
        self.assertEqual(result["target"], {
            "role": self.role, "field": "blockers", "index": 0,
            "artifact_sha256": digest, "text": self.record["review"]["blockers"][0],
        })
        self.assertEqual(self.report.read_bytes(), report_bytes)

    def test_rejects_self_challenge_and_invalid_item(self):
        self.write_report()
        with self.assertRaisesRegex(ValueError, "different ARC role"):
            self.challenge(challenger=self.role)
        with self.assertRaisesRegex(ValueError, "outside"):
            self.challenge(index=1)

    def test_rejects_unresolved_review(self):
        self.record["status"] = "invalid_response"
        self.write_report()
        with self.assertRaisesRegex(ValueError, "no current valid review"):
            self.challenge()
