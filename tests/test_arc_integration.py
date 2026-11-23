"""Exercise ARC artifact handoffs through the shipped offline CLI commands."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from warwagon.arc import ROLES


REPO = Path(__file__).resolve().parents[1]
ROLE = "distributed-systems"
BLOCKER = "The documentation decision needs a concrete revision example."


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ArcIntegrationTests(unittest.TestCase):
    def run_module(self, module, *args, expected_code=0):
        completed = subprocess.run(
            [sys.executable, "-B", "-m", f"warwagon.{module}", *map(str, args)],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(
            completed.returncode, expected_code,
            f"{module}: {completed.stderr or completed.stdout}",
        )
        return completed.stdout

    def test_real_cli_artifact_handoffs_preserve_and_verify_evidence(self):
        with TemporaryDirectory(prefix="arc integration ") as directory:
            root = Path(directory)
            first = root / "first pass.json"
            report = root / "report.json"
            challenge = root / "challenge.json"
            evidence = root / "revision example.txt"
            response = root / "response.json"
            disposition = root / "disposition.json"
            first.write_text(json.dumps({
                "kind": "real_model_first_pass_reviews",
                "schema_version": 1,
                "proposal_sha256": hashlib.sha256(b"Documentation proposal").hexdigest(),
                "reviews": [
                    {
                        "role": role,
                        "status": "valid",
                        "review": {
                            "verdict": "conditional",
                            "strengths": [],
                            "blockers": [BLOCKER] if role == ROLE else [],
                            "experiments": [],
                            "unknowns": [],
                        },
                    }
                    for role in ROLES
                ],
            }), encoding="utf-8")
            evidence.write_bytes(b"Documentation at revision A.\r\n")

            self.run_module("arc_report", first, "--output", report)
            self.run_module(
                "arc_challenge", report, "--role", ROLE, "--field", "blockers",
                "--index", 0, "--challenger", "research-skeptic",
                "--challenge", "The revision boundary is unclear.",
                "--requested-evidence", "Provide a revision example.", "--output", challenge,
            )
            self.run_module(
                "arc_evidence", challenge, "--responder", ROLE,
                "--response", "The attachment describes revision A.",
                "--evidence", evidence, "--output", response,
            )
            sources = (first, report, challenge, response, evidence)
            before = {path: sha256(path) for path in sources}
            challenge_record = json.loads(challenge.read_bytes())
            self.assertEqual(challenge_record["report_sha256"], before[report])
            self.assertEqual(challenge_record["target"]["artifact_sha256"], before[first])
            self.assertEqual(challenge_record["target"]["text"], BLOCKER)
            self.assertEqual(json.loads(response.read_bytes())["challenge_sha256"], before[challenge])

            verify_args = (response, "--challenge", challenge, "--evidence", 1, evidence)
            verification = json.loads(self.run_module("arc_verify", *verify_args))
            self.assertTrue(verification["verified"])
            self.assertEqual(verification["response_sha256"], before[response])
            self.assertEqual(verification["evidence"][0]["actual_sha256"], before[evidence])

            self.run_module(
                "arc_disposition", challenge, response,
                "--maintainer", "test maintainer", "--outcome", "addressed",
                "--rationale", "Revision A is now documented.", "--output", disposition,
            )
            outcome = json.loads(disposition.read_bytes())
            self.assertEqual(outcome["evidence_response_sha256"], before[response])
            self.assertEqual(outcome["challenge_sha256"], before[challenge])
            self.assertEqual(outcome["outcome"], "addressed")
            self.assertEqual({path: sha256(path) for path in sources}, before)
            self.assertEqual(json.loads(challenge.read_bytes())["status"], "open")

            evidence.write_bytes(b"Documentation at revision B.\r\n")
            rejected = json.loads(self.run_module("arc_verify", *verify_args, expected_code=1))
            self.assertFalse(rejected["verified"])
            self.assertEqual(rejected["evidence"][0]["status"], "mismatch")
