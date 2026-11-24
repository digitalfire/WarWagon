"""API contract and tamper rejection tests for the recorded evidence gateway."""
import json
import tempfile
from http.server import ThreadingHTTPServer
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen, Request

from warwagon.console_api import DEFAULT_FIXTURES, RUNS, events, load_bundle, make_handler, summarize

class RecordedAPITest(unittest.TestCase):
    def test_real_fixture_and_model_verdict(self):
        for name in RUNS:
            bundle = load_bundle(DEFAULT_FIXTURES, name)
            self.assertEqual(summarize(bundle)["modelVerdict"], "verified")
            self.assertEqual(summarize(bundle)["tokens"], 779 if name == "confirmation" else summarize(bundle)["tokens"])
            self.assertEqual([e["kind"] for e in events(bundle)],
                             ["tool_call", "observation", "claim", "verification", "verification"])
            self.assertEqual(bundle["verifications"][1]["claim_source"], "supplied")
            self.assertFalse(bundle["verifications"][1]["verified"])

    def test_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for item in RUNS["confirmation"]:
                p = root / item
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes((DEFAULT_FIXTURES / item).read_bytes())
            p = root / "trace.json"
            broken = json.loads(p.read_text())
            broken["observation"]["status_code"] = 201
            p.write_text(json.dumps(broken))
            with self.assertRaisesRegex(ValueError, "observation digest mismatch"):
                load_bundle(root, "confirmation")
            p.write_bytes((DEFAULT_FIXTURES / "trace.json").read_bytes())
            report = root / "model-verdict.json"
            data = json.loads(report.read_text())
            data["trace_sha256"] = "0" * 64
            report.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "verifier trace binding"):
                load_bundle(root, "confirmation")

    def test_http_routes_and_replay(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(DEFAULT_FIXTURES))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(url + "/api/v1/runs") as response:
                records = json.load(response)
                self.assertEqual(len(records["runs"]), 2)
                self.assertEqual(records["source"], "recorded")
            with urlopen(url + "/api/v1/runs/confirmation") as response:
                run = json.load(response)
                self.assertEqual(run["trace"]["observation"]["status_code"], 204)
            with urlopen(url + "/api/v1/runs/confirmation/events") as response:
                stream = response.read().decode()
                self.assertIn("event: replay_complete", stream)
                self.assertIn("event: record", stream)
                self.assertIn('"kind":"observation"', stream)
            with self.assertRaises(HTTPError) as exc:
                urlopen(Request(url + "/api/v1/runs", data=b"{}", method="POST"))
            self.assertEqual(exc.exception.code, 405)
            with self.assertRaises(HTTPError) as exc:
                urlopen(url + "/api/v1/runs/../../secrets")
            self.assertEqual(exc.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

if __name__ == "__main__":
    unittest.main()
