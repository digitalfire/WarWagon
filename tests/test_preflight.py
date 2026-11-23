import unittest
from warwagon.preflight import check

class PreflightTests(unittest.TestCase):
    def test_valid_object_form(self):
        class Model:
            model="mock"
            base_url="http://127.0.0.1:11434/v1"
            def complete(self,messages,tools=None):
                return {"choices":[{"message":{"role":"assistant","tool_calls":[{"function":{"name":"report_probe","arguments":{"message":"warwagon-ok"}}}]}}]}
        self.assertTrue(check(Model())["tool_call_correct"])
    def test_invalid_text_only_response(self):
        class Model:
            model="mock"
            base_url="http://127.0.0.1:11434/v1"
            def complete(self,messages,tools=None):
                return {"choices":[{"message":{"role":"assistant","content":"warwagon-ok"}}]}
        self.assertFalse(check(Model())["tool_call_correct"])
