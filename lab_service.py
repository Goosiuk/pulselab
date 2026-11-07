import argparse
import json
import math
import time
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


def make_handler(mode, delay):
    class LabHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path
            status = 404
            if path in ("/", "/health"):
                if mode == "slow":
                    time.sleep(delay)
                status = 503 if mode == "error" else 200
            body = json.dumps(
                {"service": "pulselab", "mode": mode, "status": status},
                ensure_ascii=False,
            ).encode("utf-8")
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
            print(
                json.dumps(
                    {
                        "ts": datetime.now(UTC).isoformat(),
                        "path": path,
                        "status": status,
                        "mode": mode,
                    }
                ),
                flush=True,
            )

        def log_message(self, format_string, *args):
            pass

    return LabHandler


def create_server(bind="127.0.0.1", port=8765, mode="healthy", delay=1.5):
    return ThreadingHTTPServer((bind, port), make_handler(mode, delay))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Тестовый HTTP-сервис")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--mode", choices=("healthy", "error", "slow"), default="healthy")
    parser.add_argument("--delay", type=float, default=1.5)
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("port должен быть от 0 до 65535; 0 выбирает свободный порт")
    if not math.isfinite(args.delay) or args.delay < 0:
        parser.error("delay должен быть конечным неотрицательным числом")
    with create_server(args.bind, args.port, args.mode, args.delay) as server:
        print(json.dumps({"event": "started", "address": server.server_address}), flush=True)
        try:
            server.serve_forever(poll_interval=0.1)
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
