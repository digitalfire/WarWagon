"""Live local lab producer tests. The model below is a test double, not an LLM."""
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import urlopen

from warwagon.console_api import DEFAULT_FIXTURES, make_handler
from warwagon.engagement_store import EngagementLedger
from warwagon.live_lab import run_local_lab


class ScriptedTestDouble:
    model = "scripted-test-double"

    def __init__(self):
        self.calls = 0

    def complete(self, messages, tools=None):
        self.calls += 1
        if self.calls == 1:
            return {
                "choices": [{"message": {
                    "role": "assistant", "content": None,
                    "tool_calls": [{"id": "call-test", "type": "function",
                                    "function": {"name": "lab_http_get", "arguments":
                                                 '{"path":"/search?q=%3Cb%3EWW_MARKER%3C%2Fb%3E"}'}}],
                }}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 40, "total_tokens": 140},
            }
        return {
            "choices": [{"message": {
                "role": "assistant", "content":
                    "Observed reflected HTML markup at /search; the markup was not encoded.",
            }}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
        }


class FailingTestDouble:
    model = "failing-test-double"

    def complete(self, messages, tools=None):
        raise RuntimeError("inference unavailable")


class LocalRunEventsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "events.sqlite"
        self.ledger = EngagementLedger(self.db)

    def test_genuine_tool_loop_contract_persists_discrete_events(self):
        result = run_local_lab(ScriptedTestDouble(), self.ledger, max_steps=3)
        self.assertEqual(result["state"], "completed")
        self.assertTrue(result["agentDiscoveryHeuristic"]["credited"])
        self.assertTrue(result["fixtureOracle"]["fixture_has_html_encoding_issue"])
        eid = result["engagementId"]
        recovered = EngagementLedger(self.db)
        records = recovered.events(eid)
        kinds = [record["kind"] for record in records]
        for kind in ("model.response", "tool.invocation", "tool.observation", "agent.final",
                     "fixture.oracle.result", "agent.discovery.heuristic",
                     "run.finished", "engagement.completed"):
            self.assertIn(kind, kinds)
        observation = next(record for record in records
                           if record["kind"] == "tool.observation")
        self.assertEqual(observation["payload"]["result"]["status"], 200)
        self.assertIn("<b>WW_MARKER</b>", observation["payload"]["result"]["body"])
        self.assertEqual(result["usage"]["total_tokens"], 210)

    def test_failed_model_does_not_leave_engagement_running(self):
        with self.assertRaisesRegex(RuntimeError, "inference unavailable"):
            run_local_lab(FailingTestDouble(), self.ledger)
        engagement = self.ledger.list_engagements()[0]
        self.assertEqual(engagement["state"], "failed")
        kinds = [event["kind"] for event in self.ledger.events(engagement["id"])]
        self.assertIn("run.failed", kinds)
        self.assertEqual(kinds[-1], "engagement.failed")
        self.assertNotIn("tool.observation", kinds)

    def test_recorded_events_available_through_sse_gateway(self):
        result = run_local_lab(ScriptedTestDouble(), self.ledger)
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            make_handler(DEFAULT_FIXTURES, engagement_db=self.db, stream_seconds=0.2)
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with urlopen(base + "/api/v1/engagements/" + result["engagementId"], timeout=3) as response:
                record = json.load(response)
                self.assertEqual(record["engagement"]["state"], "completed")
            with urlopen(base + "/api/v1/engagements/" + result["engagementId"] + "/events", timeout=3) as response:
                streamed = response.read().decode()
            self.assertIn('"kind":"tool.observation"', streamed)
            self.assertIn('"kind":"agent.discovery.heuristic"', streamed)
            self.assertIn("event: engagement.event", streamed)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
