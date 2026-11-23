import json
import unittest
from warwagon.lab import FixtureServer, LabTool, verify_finding
from warwagon.agent import AgentRunner
from warwagon.model import ChatModel

class FakeModel:
    model="scripted-test-double"
    def __init__(self): self.calls=0
    def complete(self,messages,tools=None):
        self.calls+=1
        if self.calls==1:
            return {"choices":[{"message":{"role":"assistant","content":None,"tool_calls":[{"id":"test-1","type":"function","function":{"name":"lab_http_get","arguments":json.dumps({"path":"/search?q=%3Cb%3EWW_PROBE%3C%2Fb%3E"})}}]}}],"usage":{"total_tokens":12}}
        return {"choices":[{"message":{"role":"assistant","content":"Saw HTML markup reflected on /search"}}],"usage":{"total_tokens":6}}

class LocalLabTests(unittest.TestCase):
    def test_lab_is_local_and_has_safe_control(self):
        with FixtureServer() as srv:
            tool=LabTool(srv.port)
            self.assertEqual(tool.get("/").get("status"),200)
            self.assertEqual(tool.get("http://example.com/").get("error"),"invalid_relative_path")
            self.assertEqual(tool.get("//example.com/").get("error"),"invalid_relative_path")
            self.assertEqual(tool.get("/admin").get("error"),"outside_fixture_allowlist")
            verdict=verify_finding(srv.port)
            self.assertTrue(verdict["fixture_has_html_encoding_issue"])
            self.assertTrue(verdict["control_page_encoded"])
    def test_agent_executes_real_http_tool_contract(self):
        with FixtureServer() as srv:
            output=AgentRunner(FakeModel(),LabTool(srv.port)).run("inspect lab")
            self.assertEqual(output["trace"][0]["kind"],"tool")
            self.assertIn("<b>WW_PROBE</b>",output["trace"][0]["result"]["body"])
            self.assertEqual(output["usage"]["total_tokens"],18)
    def test_model_requires_valid_transport(self):
        with self.assertRaises(ValueError):
            ChatModel("http://example.org/v1","sample")
        with self.assertRaises(ValueError):
            ChatModel("file:///tmp/test","sample")

if __name__=="__main__":unittest.main()
