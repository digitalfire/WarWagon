from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from unittest import TestCase
from unittest.mock import patch

from warwagon.http_probe import probe


class HttpProbeTests(TestCase):
    def test_records_one_root_head_without_following_redirect(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_HEAD(self):
                requests.append((self.command, self.path, self.headers.get("Authorization")))
                self.send_response(302)
                self.send_header("Location", "/another-page")
                self.end_headers()

            def log_message(self, *args):
                pass

        with HTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                result = probe(server.server_port)
            finally:
                server.shutdown()
                thread.join()
        self.assertEqual(requests, [("HEAD", "/", None)])
        self.assertEqual(result["status_code"], 302)
        self.assertEqual(result["redirects_followed"], 0)
        self.assertEqual(result["remote_ip"], "127.0.0.1")
        self.assertIsNone(result["error_type"])

    @patch("warwagon.http_probe.HTTPConnection")
    def test_records_connection_failure_without_retrying(self, connection):
        connection.return_value.connect.side_effect = ConnectionRefusedError
        result = probe(8080)
        self.assertIsNone(result["status_code"])
        self.assertEqual(result["error_type"], "ConnectionRefusedError")
        connection.return_value.connect.assert_called_once()
        connection.return_value.request.assert_not_called()
