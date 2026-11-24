import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from warwagon.evidence_smoke import FIXTURE_URL, TOOL_NAME, digest, main, run, verify


OBSERVATION = {
    "method": "HEAD", "url": FIXTURE_URL, "status_code": 204,
    "redirects_followed": 0, "error_type": None,
}
EXPECTED = {"kind": "benign_head_expectation", "schema_version": 1, "status_code": 204}
CORRECT = {"observation_sha256": digest(OBSERVATION), "status_code": 204}
RUN_RECORD = {
    "kind": "benign_head_evidence_run", "schema_version": 1,
    "tool_call": {"id": "call-fixture", "type": "function", "function": {"name": TOOL_NAME, "arguments": "{}"}},
    "observation": OBSERVATION, "observation_sha256": digest(OBSERVATION),
    "claim": CORRECT,
}


class Reviewer:
    model = "fixture-test"

    def __init__(self, selection=True):
        self.selection = selection
        self.calls = []

    def complete(self, messages, tools=None):
        self.calls.append((messages, tools))
        if self.selection:
            fields = {"tool_calls": [{
                "id": "call-fixture",
                "function": {"name": TOOL_NAME, "arguments": {}},
            }]}
            finish = "tool_calls"
        else:
            fields = {"content": json.dumps(CORRECT)}
            finish = "stop"
        return {"choices": [{"message": fields, "finish_reason": finish}], "usage": {"total_tokens": 10}}


class EvidenceSmokeTests(TestCase):
    @patch("warwagon.evidence_smoke.probe", return_value=OBSERVATION)
    def test_resume_reuses_head_and_replays_the_exact_observation(self, probe):
        with TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.sqlite"
            first = Reviewer()
            self.assertEqual(
                run(first, checkpoint, stop_after_observation=True),
                {"status": "observation_saved", "observation_reused": False},
            )
            self.assertNotIn("204", json.dumps(first.calls))
            second = Reviewer(selection=False)
            result = run(second, checkpoint)
            self.assertTrue(result["observation_reused"])
            self.assertEqual(result["tool_invocation"]["finish_reason"], "tool_calls")
            self.assertEqual(result["claim_invocation"]["finish_reason"], "stop")
            self.assertTrue(verify(result, EXPECTED)["verified"])
            self.assertEqual(len(second.calls), 1)
            messages, tools = second.calls[0]
            self.assertIsNone(tools)
            self.assertEqual(json.loads(messages[-1]["content"]), CORRECT)
            probe.assert_called_once()
            self.assertTrue(run(second, checkpoint)["claim_reused"])
            self.assertEqual(len(second.calls), 1)

    @patch("warwagon.evidence_smoke.probe")
    def test_rejects_model_output_without_the_fixed_tool_before_network(self, probe):
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "fixed fixture tool"):
                run(Reviewer(selection=False), Path(directory) / "checkpoint.sqlite")
        probe.assert_not_called()

    def test_verifier_rejects_wrong_status_wrong_reference_and_changed_observation(self):
        record = RUN_RECORD
        self.assertTrue(verify(record, EXPECTED)["verified"])
        for unsupported in ({**CORRECT, "status_code": 200}, {**CORRECT, "observation_sha256": "wrong"}):
            with self.subTest(unsupported=unsupported):
                self.assertEqual(verify(record, EXPECTED, unsupported), {
                    "verified": False, "reason": "claim_not_supported", "claim_source": "supplied",
                })
        changed = {**record, "observation": {**OBSERVATION, "status_code": 200}}
        self.assertEqual(verify(changed, EXPECTED)["reason"], "invalid_observation")
        self.assertEqual(verify(record, {**EXPECTED, "status_code": 200})["reason"], "fixture_status_mismatch")


    @patch("warwagon.evidence_smoke.probe", return_value=OBSERVATION)
    def test_interruption_during_claim_keeps_observation_committed(self, probe):
        with TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.sqlite"
            with patch("warwagon.evidence_smoke.make_claim", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    run(Reviewer(), checkpoint)
            result = run(Reviewer(selection=False), checkpoint)
            self.assertTrue(result["observation_reused"])
            self.assertFalse(result["claim_reused"])
            self.assertTrue(verify(result, EXPECTED)["verified"])
            probe.assert_called_once()


    def test_verifier_rejects_altered_fixture_tool_call(self):
        modified = {
            **RUN_RECORD,
            "tool_call": {"id": "call-fixture", "function": {"name": TOOL_NAME, "arguments": '{"port": 4280}'}},
        }
        self.assertEqual(verify(modified, EXPECTED)["reason"], "invalid_fixture_tool_call")

    def test_cli_links_failed_verdict_to_exact_input_bytes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            trace, expected, claim, outcome = (root / name for name in ("trace", "expected", "claim", "result"))
            for path, value in (
                (trace, RUN_RECORD), (expected, EXPECTED), (claim, {**CORRECT, "status_code": 200}),
            ):
                path.write_bytes(json.dumps(value, indent=2).encode() + b"\r\n")
            with patch("sys.argv", [
                "evidence_smoke", "verify", str(trace), "--expected", str(expected),
                "--claim", str(claim), "--output", str(outcome),
            ]):
                self.assertEqual(main(), 1)
            result = json.loads(outcome.read_bytes())
            self.assertFalse(result["verified"])
            for field, path in (
                ("trace_sha256", trace), ("expectation_sha256", expected), ("supplied_claim_sha256", claim),
            ):
                self.assertEqual(result[field], hashlib.sha256(path.read_bytes()).hexdigest())
