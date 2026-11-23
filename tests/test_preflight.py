import unittest
from unittest.mock import patch

from warwagon.preflight import check


class Model:
    model = "requested"
    base_url = "http://127.0.0.1:11434/v1"

    def __init__(self, response):
        self.response = response

    def complete(self, messages, tools=None):
        return self.response


def tool(arguments, **fields):
    return {"function": {"name": "report_probe", "arguments": arguments}, **fields}


def completion(calls):
    return {"choices": [{"message": {"tool_calls": calls}, "finish_reason": "tool_calls"}]}


class PreflightTests(unittest.TestCase):
    def test_accepts_structured_arguments_in_both_provider_encodings(self):
        for arguments in ({"message": "warwagon-ok"}, '{"message": "warwagon-ok"}'):
            with self.subTest(arguments=arguments):
                result = check(Model(completion([tool(arguments)])))
                self.assertTrue(result["tool_call_correct"])
                self.assertEqual(result["calls"][0]["arguments"], {"message": "warwagon-ok"})

    def test_rejects_wrong_argument_shapes_and_extra_fields(self):
        for arguments in ("{", "[]", "null", [1], {"message": 1}, {"message": "warwagon-ok", "extra": True}):
            with self.subTest(arguments=arguments):
                result = check(Model(completion([tool(arguments)])))
                self.assertTrue(result["tool_call_seen"])
                self.assertFalse(result["tool_call_correct"])

    def test_rejects_extra_calls_and_unexpected_call_type(self):
        expected = tool({"message": "warwagon-ok"})
        for calls in ([expected, expected], [tool({"message": "warwagon-ok"}, type="unknown")]):
            with self.subTest(calls=calls):
                self.assertFalse(check(Model(completion(calls)))["tool_call_correct"])

    def test_text_only_response_fails_without_reporting_a_call(self):
        result = check(Model({"choices": [{"message": {"content": "warwagon-ok"}}]}))
        self.assertFalse(result["tool_call_seen"])
        self.assertFalse(result["tool_call_correct"])

    def test_malformed_envelopes_have_a_diagnostic(self):
        for response in (
            {"choices": {}},
            {"choices": [None]},
            {"choices": [{"message": "text"}]},
            completion({"function": "wrong container"}),
            completion([None, {"function": "wrong object"}]),
        ):
            with self.subTest(response=response):
                result = check(Model(response))
                self.assertFalse(result["tool_call_correct"])
                self.assertTrue(result["diagnostic"].startswith("fail:"))

    def test_response_provenance_and_elapsed_time(self):
        response = completion([tool({"message": "warwagon-ok"})])
        response.update(id="completion-id", model="served", usage={"total_tokens": 3})
        with patch("warwagon.preflight.time.monotonic", side_effect=[3.0, 3.5]):
            result = check(Model(response))
        self.assertEqual(result["model"], "requested")
        self.assertEqual(result["response_model"], "served")
        self.assertEqual(result["response_id"], "completion-id")
        self.assertEqual(result["finish_reason"], "tool_calls")
        self.assertEqual(result["elapsed_seconds"], 0.5)
        self.assertEqual(result["usage"], {"total_tokens": 3})

    def test_endpoint_provenance_omits_query_and_fragment(self):
        model = Model(completion([]))
        model.base_url = "https://model.example/v1?token=example#fragment"
        self.assertEqual(check(model)["endpoint"], "https://model.example/v1")
