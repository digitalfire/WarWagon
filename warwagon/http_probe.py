"""Record a single unauthenticated HEAD request to an IPv4 loopback root."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
from http.client import HTTPConnection, HTTPException
import json
from pathlib import Path
from time import monotonic


def probe(port):
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    host = "127.0.0.1"
    trace = {
        "kind": "local_http_connectivity_trace",
        "schema_version": 1,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "method": "HEAD",
        "url": f"http://{host}:{port}/",
        "status_code": None,
        "redirects_followed": 0,
        "connect_seconds": None,
        "response_headers_seconds": None,
        "error_type": None,
    }
    started = monotonic()
    try:
        with closing(HTTPConnection(host, port, timeout=5)) as connection:
            connection.connect()
            trace["connect_seconds"] = round(monotonic() - started, 6)
            trace["remote_ip"], trace["remote_port"] = connection.sock.getpeername()
            connection.request("HEAD", "/")
            with closing(connection.getresponse()) as response:
                trace["response_headers_seconds"] = round(monotonic() - started, 6)
                trace["status_code"] = response.status
                trace["http_version"] = {10: "1.0", 11: "1.1"}.get(response.version)
    except (OSError, HTTPException) as exc:
        trace["error_type"] = type(exc).__name__
    trace["total_seconds"] = round(monotonic() - started, 6)
    return trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("output already exists")
        result = probe(args.port)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(result, output, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")
    return 0 if result["status_code"] is not None and result["error_type"] is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
