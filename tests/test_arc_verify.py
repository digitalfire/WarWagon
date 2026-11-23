import hashlib
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from warwagon.arc_evidence import build_evidence_response
from warwagon.arc_verify import main, verify_response


class VerifyResponseTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.challenge = self.root / "challenge.json"
        self.response = self.root / "response.json"
        self.original = self.root / "artifact path.bin"
        self.original.write_bytes(b"one\r\n")
        self.challenge.write_text(json.dumps({
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
                "text": "Provide evidence.",
            },
            "challenge": "Which version?",
            "requested_evidence": "Provide the original output.",
        }), encoding="utf-8")
        payload = build_evidence_response(
            self.challenge, "distributed-systems", "Original output.", [self.original],
        )
        self.response.write_text(json.dumps(payload), encoding="utf-8")

    def test_verifies_exact_bytes_from_an_explicit_relocated_file(self):
        remapped = self.root / "other location.bin"
        contents = self.original.read_bytes()
        self.original.unlink()
        remapped.write_bytes(contents)
        source_bytes = [path.read_bytes() for path in (self.response, self.challenge, remapped)]

        report = verify_response(self.response, {1: remapped}, self.challenge)

        self.assertTrue(report["verified"])
        self.assertEqual(report["response_sha256"], hashlib.sha256(source_bytes[0]).hexdigest())
        self.assertEqual(report["challenge"]["status"], "match")
        self.assertEqual(report["evidence"][0], {
            "index": 1,
            "status": "match",
            "expected_sha256": hashlib.sha256(contents).hexdigest(),
            "actual_sha256": hashlib.sha256(contents).hexdigest(),
            "expected_size_bytes": len(contents),
            "actual_size_bytes": len(contents),
        })
        self.assertEqual([path.read_bytes() for path in (self.response, self.challenge, remapped)], source_bytes)

    def test_never_uses_embedded_path_and_marks_explicit_missing_file(self):
        for paths in ({}, {1: self.root / "missing.txt"}):
            with self.subTest(paths=paths):
                report = verify_response(self.response, paths)
                self.assertFalse(report["verified"])
                self.assertEqual(report["evidence"][0]["status"], "missing")
                self.assertEqual(report["challenge"]["status"], "not_checked")

    def test_one_byte_change_and_wrong_recorded_size_are_mismatches(self):
        changed = self.root / "changed.bin"
        changed.write_bytes(b"two\r\n")
        report = verify_response(self.response, {1: changed})
        evidence = report["evidence"][0]
        self.assertFalse(report["verified"])
        self.assertEqual(evidence["status"], "mismatch")
        self.assertEqual(evidence["actual_size_bytes"], evidence["expected_size_bytes"])
        self.assertNotEqual(evidence["actual_sha256"], evidence["expected_sha256"])

        payload = json.loads(self.response.read_bytes())
        payload["evidence"][0]["size_bytes"] += 1
        self.response.write_text(json.dumps(payload), encoding="utf-8")
        report = verify_response(self.response, {1: self.original})
        self.assertEqual(report["evidence"][0]["status"], "mismatch")

    def test_optional_challenge_checks_exact_bytes_and_proposal(self):
        self.assertTrue(verify_response(self.response, {1: self.original})["verified"])
        self.challenge.write_bytes(self.challenge.read_bytes() + b"\n")
        report = verify_response(self.response, {1: self.original}, self.challenge)
        self.assertFalse(report["verified"])
        self.assertEqual(report["challenge"]["status"], "mismatch")
        self.assertTrue(report["challenge"]["proposal_matches"])

        payload = json.loads(self.response.read_bytes())
        payload["proposal_sha256"] = "d" * 64
        payload["challenge_sha256"] = hashlib.sha256(self.challenge.read_bytes()).hexdigest()
        self.response.write_text(json.dumps(payload), encoding="utf-8")
        report = verify_response(self.response, {1: self.original}, self.challenge)
        self.assertFalse(report["verified"])
        self.assertEqual(report["challenge"]["status"], "mismatch")
        self.assertFalse(report["challenge"]["proposal_matches"])

    def test_cli_reports_0_for_match_1_for_missing_and_2_for_invalid_input(self):
        command = ["arc_verify", str(self.response)]
        for extra, expected in [
            (["--evidence", "1", str(self.original)], 0),
            ([], 1),
        ]:
            with patch("sys.argv", command + extra), patch("sys.stdout", new_callable=StringIO) as output:
                self.assertEqual(main(), expected)
                self.assertEqual(json.loads(output.getvalue())["verified"], expected == 0)

        for extra in [
            ["--evidence", "2", str(self.original)],
            ["--evidence", "1", str(self.original)] * 2,
        ]:
            with patch("sys.argv", command + extra), patch("sys.stderr", new_callable=StringIO):
                with self.assertRaises(SystemExit) as failure:
                    main()
                self.assertEqual(failure.exception.code, 2)

        self.response.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "expected an ARC v1"):
            verify_response(self.response, {1: self.original})
