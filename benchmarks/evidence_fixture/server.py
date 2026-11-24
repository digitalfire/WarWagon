"""Benign fixture for a known HEAD observation."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import os


class FixtureHandler(BaseHTTPRequestHandler):
    status = 204

    def do_HEAD(self):
        self.send_response(self.status if self.path == "/" else 404)
        self.end_headers()


if __name__ == "__main__":
    FixtureHandler.status = int(os.environ.get("FIXTURE_HEAD_STATUS", "204"))
    if FixtureHandler.status not in {200, 204, 503}:
        raise SystemExit("FIXTURE_HEAD_STATUS must be 200, 204, or 503")
    HTTPServer(("0.0.0.0", 8080), FixtureHandler).serve_forever()
