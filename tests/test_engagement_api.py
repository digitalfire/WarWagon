"""Live engagement SSE API tests using only local fixtures and a temp SQLite file."""
import json
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from warwagon.console_api import DEFAULT_FIXTURES, make_handler
from warwagon.engagement_store import EngagementLedger


class EngagementStreamingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "events.sqlite"
        self.ledger = EngagementLedger(self.path)
        self.engagement = self.ledger.create_engagement(
            "Local lab", "http://127.0.0.1:3000", engagement_id="eng-local"
        )
        self.ledger.transition(self.engagement["id"], "running")
        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            make_handler(DEFAULT_FIXTURES, engagement_db=self.path, stream_seconds=0.45)
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.addCleanup(lambda: self.thread.join(timeout=3))

    def _get(self, path, headers=None):
        request = Request(self.base + path, headers=headers or {})
        with urlopen(request, timeout=5) as response:
            return response.status, response.headers, response.read().decode()

    @staticmethod
    def _records(stream):
        return [json.loads(line[6:]) for line in stream.splitlines() if line.startswith("data: ")]

    def test_list_and_detail_retain_separate_recorded_source(self):
        status, _, raw = self._get("/api/v1/engagements")
        self.assertEqual(status, 200)
        data = json.loads(raw)
        self.assertEqual(len(data["engagements"]), 1)
        self.assertEqual(data["source"], "recorded")
        status, _, raw = self._get("/api/v1/engagements/eng-local")
        self.assertEqual(status, 200)
        detail = json.loads(raw)
        self.assertEqual(detail["engagement"]["state"], "running")
        self.assertEqual([x["kind"] for x in detail["events"]],
                         ["engagement.created", "engagement.running"])
        status, _, raw = self._get("/api/v1/runs")
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(raw)["runs"]), 2)

    def test_sse_replay_supports_initial_and_last_event_cursor(self):
        all_events = self.ledger.events("eng-local")
        first, second = [e["sequence"] for e in all_events]
        status, headers, stream = self._get("/api/v1/engagements/eng-local/events?after=0")
        self.assertEqual(status, 200)
        self.assertIn("text/event-stream", headers["Content-Type"])
        self.assertIn(f"id: {first}", stream)
        self.assertIn(f"id: {second}", stream)
        self.assertEqual([r["eventId"] for r in self._records(stream)],
                         ["engagement.created", "transition:running"])
        _, _, stream = self._get(
            "/api/v1/engagements/eng-local/events?after=0",
            {"Last-Event-ID": str(first)}
        )
        self.assertEqual([r["sequence"] for r in self._records(stream)], [second])

    def test_stream_tails_external_writer_while_connection_is_open(self):
        def producer():
            import time
            time.sleep(0.08)
            EngagementLedger(self.path).append(
                "eng-local", "agent.tool.called", {"tool": "lab_http_get"},
                origin="tool", event_id="call-001",
            )
        thread = threading.Thread(target=producer)
        thread.start()
        _, _, stream = self._get("/api/v1/engagements/eng-local/events",
                                 {"Last-Event-ID": str(self.ledger.events("eng-local")[-1]["sequence"])})
        thread.join(timeout=3)
        self.assertIn('"kind":"agent.tool.called"', stream)
        self.assertIn('"eventId":"call-001"', stream)

    def test_invalid_cursors_and_unknown_engagement_rejected(self):
        for path in (
            "/api/v1/engagements/eng-local/events?after=-1",
            "/api/v1/engagements/eng-local/events?after=abc",
            "/api/v1/engagements/eng-local/events?after=1&after=2",
            "/api/v1/engagements/eng-local/events?unexpected=x",
        ):
            with self.assertRaises(HTTPError) as exc:
                self._get(path)
            self.assertEqual(exc.exception.code, 400)
        with self.assertRaises(HTTPError) as exc:
            self._get("/api/v1/engagements/missing/events")
        self.assertEqual(exc.exception.code, 404)
        with self.assertRaises(HTTPError) as exc:
            urlopen(Request(self.base + "/api/v1/engagements",
                            data=b"{}", method="POST"), timeout=4)
        self.assertEqual(exc.exception.code, 405)


if __name__ == "__main__":
    unittest.main()
