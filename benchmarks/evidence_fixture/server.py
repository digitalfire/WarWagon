"""Benign fixture for a known HEAD observation."""

from http.server import BaseHTTPRequestHandler, HTTPServer


class FixtureHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(204 if self.path == "/" else 404)
        self.end_headers()


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), FixtureHandler).serve_forever()
