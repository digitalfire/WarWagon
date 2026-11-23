import unittest
from warwagon.arc import ROLES, review

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
        self.assertNotIn("private diagnostic", str(result))
