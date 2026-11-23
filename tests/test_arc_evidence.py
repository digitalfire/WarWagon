import hashlib
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from warwagon.arc_evidence import build_evidence_response, main


class EvidenceResponseTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.challenge = self.root / "challenge.json"
        self.evidence = self.root / "test.txt"
        self.output = self.root / "response.json"
        self.payload = {
            "kind": "arc_review_challenge",
            "schema_version": 1,
            "status": "open",
            "proposal_sha256": "a" * 64,
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
            "requested_evidence": "Provide test logs for this revision.",
        }
        self.challenge.write_bytes(json.dumps(self.payload).encode() + b"\r\n")
        self.evidence.write_bytes(b"test passed\r\n")

    def run_cli(self, evidence_paths, response="Here is the test log."):
        command = [
            "arc_evidence", str(self.challenge), "--responder", "distributed-systems",
            "--response", response, "--output", str(self.output),
        ]
        for path in evidence_paths:
            command.extend(("--evidence", str(path)))
        with patch("sys.argv", command):
            main()

    def test_response_references_exact_challenge_and_each_evidence_file(self):
        second = self.root / "details.bin"
        second.write_bytes(b"\x00" * 65537)
        original = self.challenge.read_bytes()
        paths = [self.evidence, second]

        self.run_cli(paths)
        artifact = json.loads(self.output.read_bytes())

        self.assertEqual(artifact, {
            "kind": "arc_challenge_evidence_response",
            "schema_version": 1,
            "proposal_sha256": self.payload["proposal_sha256"],
            "challenge_sha256": hashlib.sha256(original).hexdigest(),
            "responder_role": "distributed-systems",
            "response": "Here is the test log.",
            "evidence": [
                {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                 "size_bytes": path.stat().st_size}
                for path in paths
            ],
        })
        self.assertEqual(self.challenge.read_bytes(), original)

    def test_invalid_inputs_create_no_output(self):
        original_challenge = self.challenge.read_bytes()
        original_evidence = self.evidence.read_bytes()
        for evidence, response in [
            ([], "Response"),
            ([self.evidence, self.root / "missing.txt"], "Response"),
            ([self.evidence], "  "),
        ]:
            with self.subTest(evidence=evidence, response=response):
                with patch("sys.stderr", new_callable=StringIO), self.assertRaises(SystemExit) as error:
                    self.run_cli(evidence, response)
                self.assertEqual(error.exception.code, 2)
                self.assertFalse(self.output.exists())
        self.assertEqual(self.challenge.read_bytes(), original_challenge)
        self.assertEqual(self.evidence.read_bytes(), original_evidence)

    def test_rejects_malformed_challenge(self):
        self.payload["target"]["index"] = True
        self.challenge.write_text(json.dumps(self.payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid ARC challenge target"):
            build_evidence_response(self.challenge, "distributed-systems", "Response", [self.evidence])

    def test_refuses_overwriting_evidence_or_challenge(self):
        for existing in [self.evidence, self.challenge]:
            with self.subTest(existing=existing):
                original = existing.read_bytes()
                self.output = existing
                with patch("sys.stderr", new_callable=StringIO), self.assertRaises(SystemExit) as error:
                    self.run_cli([self.evidence])
                self.assertEqual(error.exception.code, 2)
                self.assertEqual(existing.read_bytes(), original)
