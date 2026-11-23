import hashlib
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from warwagon.arc_disposition import main
from warwagon.arc_evidence import build_evidence_response


class DispositionTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.challenge = root / "challenge.json"
        self.response = root / "response.json"
        self.output = root / "disposition.json"
        self.proposal_digest = "a" * 64
        self.challenge.write_bytes(json.dumps({
            "kind": "arc_review_challenge",
            "schema_version": 1,
            "status": "open",
            "proposal_sha256": self.proposal_digest,
            "report_sha256": "b" * 64,
            "challenger_role": "research-skeptic",
            "target": {
                "role": "distributed-systems",
                "artifact_sha256": "c" * 64,
                "field": "blockers",
                "index": 0,
                "text": "Recovery claims need evidence.",
            },
            "challenge": "Which version was tested?",
            "requested_evidence": "Provide the run log.",
        }).encode() + b"\r\n")
        self.evidence = root / "run.log"
        self.evidence.write_text("Tests covered normal recovery only.", encoding="utf-8")
        self.response_record = build_evidence_response(
            self.challenge, "distributed-systems", "See the run log.", [self.evidence],
        )
        self.write_response(self.response_record)

    def write_response(self, record):
        self.response.write_bytes(json.dumps(record).encode() + b"\r\n")

    def run_cli(self, output=None, maintainer="Repo maintainer", rationale="No failure recovery was tested."):
        argv = [
            "arc_disposition", str(self.challenge), str(self.response),
            "--maintainer", maintainer, "--outcome", "needs-evidence",
            "--rationale", rationale, "--output", str(output or self.output),
        ]
        with patch("sys.argv", argv):
            main()

    def assert_cli_rejected(self, message, **kwargs):
        with patch("sys.stderr", new_callable=StringIO) as stderr, self.assertRaises(SystemExit) as exc:
            self.run_cli(**kwargs)
        self.assertEqual(exc.exception.code, 2)
        self.assertIn(message, stderr.getvalue())

    def test_records_explicit_outcome_and_exact_input_digests(self):
        challenge_bytes = self.challenge.read_bytes()
        response_bytes = self.response.read_bytes()
        self.run_cli()

        self.assertEqual(json.loads(self.output.read_bytes()), {
            "kind": "arc_challenge_disposition",
            "schema_version": 1,
            "proposal_sha256": self.proposal_digest,
            "challenge_sha256": hashlib.sha256(challenge_bytes).hexdigest(),
            "evidence_response_sha256": hashlib.sha256(response_bytes).hexdigest(),
            "maintainer": "Repo maintainer",
            "attribution": "caller-supplied",
            "outcome": "needs-evidence",
            "rationale": "No failure recovery was tested.",
        })
        self.assertEqual(self.challenge.read_bytes(), challenge_bytes)
        self.assertEqual(self.response.read_bytes(), response_bytes)

    def test_rejects_mismatched_proposal_and_changed_challenge_bytes(self):
        self.write_response({**self.response_record, "proposal_sha256": "d" * 64})
        self.assert_cli_rejected("response proposal digest does not match")
        self.write_response(self.response_record)
        self.challenge.write_bytes(self.challenge.read_bytes() + b"\n")
        self.assert_cli_rejected("response challenge digest does not match")
        self.assertFalse(self.output.exists())

    def test_rejects_malformed_response_and_blank_decision_fields(self):
        self.write_response({**self.response_record, "evidence": []})
        self.assert_cli_rejected("expected an ARC v1 challenge evidence response")
        self.write_response(self.response_record)
        self.assert_cli_rejected("must be nonblank", maintainer=" ")
        self.assert_cli_rejected("must be nonblank", rationale=" ")
        self.assertFalse(self.output.exists())

    def test_refuses_overwriting_inputs_or_existing_disposition(self):
        self.run_cli()
        for path in (self.challenge, self.response, self.evidence, self.output):
            with self.subTest(path=path):
                original = path.read_bytes()
                self.assert_cli_rejected("File exists", output=path)
                self.assertEqual(path.read_bytes(), original)
