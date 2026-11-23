import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from warwagon.arc import ROLES
from warwagon.arc_report import build_report


def valid(role, verdict):
    return {
        "role": role,
        "status": "valid",
        "review": {
            "verdict": verdict,
            "strengths": [],
            "blockers": [],
            "experiments": [],
            "unknowns": [],
        },
    }


class ReportTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.role = "research-skeptic"
        self.failed = {"role": self.role, "status": "invalid_response", "response": "Review prose"}
        records = [self.failed if role == self.role else valid(role, "support") for role in ROLES]
        self.first, self.digest = self.artifact("first", records)

    def artifact(self, name, records, proposal="same", **extra):
        path = self.root / f"{name}.json"
        payload = {
            "kind": "real_model_first_pass_reviews",
            "schema_version": 1,
            "proposal_sha256": proposal,
            "reviews": records,
            **extra,
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def test_unresolved_role_has_no_structured_verdict(self):
        report = build_report(self.first, [])
        self.assertEqual(report["unresolved_roles"], [self.role])
        self.assertFalse(report["verdicts_differ"])
        self.assertEqual(report["attempts_by_role"][self.role][0]["record"], self.failed)

    def test_retry_preserves_history_and_exposes_disagreement(self):
        retry, digest = self.artifact(
            "retry", [valid(self.role, "reject")],
            retry_of={"artifact_sha256": self.digest, "review": self.failed},
        )
        report = build_report(self.first, [retry])
        self.assertEqual(report["unresolved_roles"], [])
        self.assertEqual(report["verdict_roles"]["reject"], [self.role])
        self.assertTrue(report["verdicts_differ"])
        self.assertEqual(
            [a["artifact_sha256"] for a in report["attempts_by_role"][self.role]],
            [self.digest, digest],
        )

    def test_rejects_changed_proposal_and_tampered_parent(self):
        link = {"artifact_sha256": self.digest, "review": self.failed}
        changed, _ = self.artifact("changed", [valid(self.role, "reject")], "other", retry_of=link)
        with self.assertRaisesRegex(ValueError, "different proposal"):
            build_report(self.first, [changed])
        link["review"] = {**self.failed, "response": "rewritten"}
        tampered, _ = self.artifact("tampered", [valid(self.role, "reject")], retry_of=link)
        with self.assertRaisesRegex(ValueError, "latest unsuccessful attempt"):
            build_report(self.first, [tampered])
