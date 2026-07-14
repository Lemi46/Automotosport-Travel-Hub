# Lokalni deterministički HTTP servis za testiranje sinhronizacije bez interneta 

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class MotorsportHandler(BaseHTTPRequestHandler):
    server_version = "AutomotosportMock/1.0"

    def _send_json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - naziv zahteva BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/health":
            self._send_json({"status": "ok"})
            return
        if parsed.path == "/f1/current.json":
            self._send_json(
                {
                    "MRData": {
                        "RaceTable": {
                            "Races": [
                                {
                                    "raceName": "UI API F1 Grand Prix",
                                    "date": "2099-07-10",
                                    "Circuit": {
                                        "circuitName": "UI API F1 Circuit",
                                        "Location": {"country": "UI Francuska"},
                                    },
                                }
                            ]
                        }
                    }
                }
            )
            return
        if parsed.path == "/motogp/seasons":
            self._send_json(
                [{"id": "ui-current-season", "year": 2026, "current": True}]
            )
            return
        if parsed.path == "/motogp/events":
            finished = query.get("isFinished", ["false"])[0].lower() == "true"
            event = {
                "id": "ui-motogp-finished" if finished else "ui-motogp-upcoming",
                "sponsored_name": (
                    "UI API MotoGP Finished" if finished else "UI API MotoGP Upcoming"
                ),
                "date_start": "2098-04-12T08:00:00+02:00" if finished else "2099-08-12T08:00:00+02:00",
                "circuit": {"name": "UI API MotoGP Circuit"},
                "country": {"name": "UI Španija"},
                "test": False,
                "kind": "GP",
            }
            self._send_json([event])
            return
        if parsed.path == "/wsbk/eventsseason.php":
            self._send_json(
                {
                    "events": [
                        {
                            "strEvent": "UI API WSBK Round",
                            "strVenue": "UI API WSBK Circuit",
                            "strCountry": "UI Holandija",
                            "dateEvent": "2099-09-16",
                        }
                    ]
                }
            )
            return

        self._send_json({"error": "not found"}, status=404)

    def log_message(self, format: str, *args) -> None:
        print(f"[mock-api] {self.address_string()} - {format % args}")


def build_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), MotorsportHandler)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    server = build_server(args.host, args.port)
    print(f"Mock API sluša na http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
