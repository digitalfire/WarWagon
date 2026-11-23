import hashlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from warwagon.arc import ROLES, main, review, validate_response
from warwagon.model import ChatModel

class MockReviewer:
    model="mock-reviewer"
    base_url="http://127.0.0.1:11434/v1"
    def __init__(self): self.messages=None
    def complete(self,messages,tools=None):
        self.messages=messages
        return {"choices":[{"message":{"content":'{"verdict":"needs-research","blockers":["missing experiment"],"strengths":[],"experiments":[],"unknowns":[]}'}}],"usage":{"total_tokens":11}}

class ReviewTests(unittest.TestCase):
    def test_all_specialists_defined(self):
        self.assertEqual(len(ROLES),9)
    def test_first_pass_is_isolated(self):
        a,b=MockReviewer(),MockReviewer()
        one=review(a,"agent-intelligence","RFC frozen")
        two=review(b,"evaluation-science","RFC frozen")
        self.assertEqual(a.messages[1]["content"],b.messages[1]["content"])
        self.assertNotEqual(a.messages[0]["content"],b.messages[0]["content"])
        self.assertEqual(one["usage"]["total_tokens"],11)
        self.assertTrue(two["independent_context"])
        self.assertEqual(one["status"], "valid")
        self.assertEqual(one["review"]["verdict"], "needs-research")

    def test_response_model_and_fingerprint_are_provider_labels(self):
        reviewer = MockReviewer()
        response = reviewer.complete([])
        response.update(model=" resolved-model ", system_fingerprint="fp_001")
        reviewer.complete = lambda messages: response
        record = review(reviewer, "evaluation-science", "Frozen")
        self.assertEqual(record["model"], "mock-reviewer")
        self.assertEqual(record["response_model"], "resolved-model")
        self.assertEqual(record["response_system_fingerprint"], "fp_001")
        response.update(model={}, system_fingerprint=" ")
        record = review(reviewer, "evaluation-science", "Frozen")
        self.assertIsNone(record["response_model"])
        self.assertIsNone(record["response_system_fingerprint"])

    @patch("warwagon.arc.ChatModel")
    def test_configured_aliases_and_reported_deployments_are_counted_separately(self, model):
        first_role, missing_role = list(ROLES)[:2]

        def make_reviewer(base_url, model, *, api_key):
            reviewer = MockReviewer()
            reviewer.base_url = base_url
            reviewer.model = model
            response = reviewer.complete([])
            if model != "unknown-alias":
                response["model"] = "provider-model"
            reviewer.complete = lambda messages: response
            return reviewer

        model.side_effect = make_reviewer
        with TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = root / "proposal.md"
            proposal.write_text("Frozen", encoding="utf-8")
            output = root / "result.json"
            profiles = root / "profiles.json"
            profiles.write_text(json.dumps({
                role: {
                    "base_url": "https://other.example/v1" if role == first_role else "http://localhost/v1",
                    "model": "unknown-alias" if role == missing_role else role,
                }
                for role in ROLES
            }), encoding="utf-8")
            with patch("sys.argv", [
                "arc", "--proposal", str(proposal), "--reviewers-file", str(profiles),
                "--output", str(output),
            ]):
                self.assertEqual(main(), 0)
            result = json.loads(output.read_bytes())
        self.assertEqual(result["configured_endpoint_model_count"], len(ROLES))
        self.assertEqual(result["observed_endpoint_model_count"], 2)
        self.assertEqual(result["roles_without_reported_model"], [missing_role])
        self.assertFalse(result["model_weight_identity_verified"])

    def test_malformed_review_is_retained_without_a_verdict(self):
        reviewer = MockReviewer()
        reviewer.complete = lambda messages: {"choices": [{"message": {"content": "{}"}}]}
        result = review(reviewer, "evaluation-science", "RFC frozen")
        self.assertEqual(result["status"], "invalid_response")
        self.assertEqual(result["response"], "{}")
        self.assertNotIn("review", result)

    def test_request_failure_does_not_echo_exception_details(self):
        reviewer = MockReviewer()

        def fail(messages):
            raise OSError("private diagnostic")

        reviewer.complete = fail
        result = review(reviewer, "evaluation-science", "RFC frozen")
        self.assertEqual(result["status"], "request_failed")
        self.assertIsNone(result["response_model"])
        self.assertIsNone(result["response_system_fingerprint"])
        self.assertNotIn("private diagnostic", str(result))

    def test_accepts_one_json_fence_and_rejects_surrounding_text(self):
        raw = MockReviewer().complete([])["choices"][0]["message"]["content"]
        fenced = "```json\n" + raw + "\n```"
        self.assertEqual(validate_response(fenced), validate_response(raw))
        with self.assertRaises(ValueError):
            validate_response("Review:\n" + fenced)

    @patch("warwagon.model.urllib.request.urlopen")
    def test_array_provider_response_does_not_escape_review(self, urlopen):
        urlopen.return_value = io.BytesIO(b"[]")
        result = review(ChatModel("http://localhost/v1", "test"), "evaluation-science", "Frozen")
        self.assertEqual(result["status"], "request_failed")

    @patch.dict("os.environ", {"WW_MODEL_API_KEY": "ambient"})
    @patch("warwagon.model.urllib.request.urlopen")
    def test_explicit_keys_do_not_inherit_ambient_key(self, urlopen):
        for key, expected in (("scoped", "Bearer scoped"), ("", None)):
            urlopen.return_value = io.BytesIO(b'{"choices":[{}]}')
            ChatModel("https://example.com/v1", "test", api_key=key).complete([])
            self.assertEqual(urlopen.call_args.args[0].get_header("Authorization"), expected)


    @patch("warwagon.arc.ChatModel")
    def test_retry_runs_one_role_and_retains_the_original_attempt(self, model):
        model.return_value = MockReviewer()
        role = "evaluation-science"
        failed_review = {"role": role, "status": "invalid_response", "response": "invalid"}
        with TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = root / "proposal.md"
            proposal.write_bytes(b"Frozen packet\r\n")
            original = root / "original.json"
            original.write_text(json.dumps({
                "kind": "real_model_first_pass_reviews",
                "schema_version": 1,
                "proposal_sha256": hashlib.sha256(proposal.read_bytes()).hexdigest(),
                "reviews": [failed_review],
            }), encoding="utf-8")
            original_bytes = original.read_bytes()
            output = root / "retry.json"
            argv = [
                "arc", "--proposal", str(proposal), "--retry-from", str(original),
                "--retry-role", role, "--model", "mock-reviewer", "--output", str(output),
            ]
            with patch("sys.argv", argv):
                self.assertEqual(main(), 0)
            result = json.loads(output.read_bytes())
            self.assertEqual([item["role"] for item in result["reviews"]], [role])
            self.assertEqual(result["retry_of"]["review"], failed_review)
            self.assertEqual(result["retry_of"]["artifact_sha256"], hashlib.sha256(original_bytes).hexdigest())
            self.assertEqual(original.read_bytes(), original_bytes)
            model.assert_called_once()

            proposal.write_bytes(b"Edited packet\n")
            argv[-1] = str(root / "second-retry.json")
            with patch("sys.argv", argv), patch("sys.stderr", new_callable=io.StringIO) as stderr:
                with self.assertRaises(SystemExit) as failure:
                    main()
                self.assertEqual(failure.exception.code, 2)
                self.assertIn("same proposal bytes", stderr.getvalue())
            model.assert_called_once()
