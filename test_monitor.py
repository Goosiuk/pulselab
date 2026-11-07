import json
import math
import socket
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import sleep

import monitor


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/slow":
            sleep(0.2)
        status = {"/ok": 200, "/error": 503, "/slow": 200}.get(self.path, 404)
        try:
            self.send_response(status)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format_string, *args):
        pass


class TestHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(
            target=cls.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
        )
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def assert_result(self, result, url, status, ok):
        for key in ("url", "status_code", "ok", "elapsed_ms", "error"):
            self.assertIn(key, result)
        self.assertEqual(result["url"], url)
        self.assertEqual(result["status_code"], status)
        self.assertIs(result["ok"], ok)
        self.assertTrue(math.isfinite(result["elapsed_ms"]))
        self.assertGreaterEqual(result["elapsed_ms"], 0)
        if ok:
            self.assertIsNone(result["error"])
        else:
            self.assertIsInstance(result["error"], str)
            self.assertTrue(result["error"])

    def test_200(self):
        url = self.base + "/ok"
        self.assert_result(monitor.check_once(url, 1), url, 200, True)

    def test_503(self):
        url = self.base + "/error"
        self.assert_result(monitor.check_once(url, 1), url, 503, False)

    def test_404(self):
        url = self.base + "/missing"
        self.assert_result(monitor.check_once(url, 1), url, 404, False)

    def test_timeout(self):
        url = self.base + "/slow"
        self.assert_result(monitor.check_once(url, 0.03), url, None, False)

    def test_connection_refused(self):
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            url = f"http://127.0.0.1:{reserved.getsockname()[1]}/health"
            self.assert_result(monitor.check_once(url, 0.3), url, None, False)


class TestSummary(unittest.TestCase):
    def test_empty_is_unknown(self):
        self.assertIsNone(monitor.availability_percent([]))

    def test_proportion(self):
        checks = [{"ok": True}, {"ok": False}, {"ok": True}]
        self.assertAlmostEqual(monitor.availability_percent(checks), 200 / 3)

    def test_all_failed(self):
        self.assertEqual(monitor.availability_percent([{"ok": False}]), 0)


class TestJSONL(unittest.TestCase):
    def test_append_preserves_previous_records(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "checks.jsonl"
            first = {"url": "http://127.0.0.1", "ok": True, "note": "сервис"}
            second = {"url": "http://127.0.0.1", "ok": False}
            before = first.copy()
            monitor.append_result(path, first)
            monitor.append_result(path, second)
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.endswith("\n"))
            self.assertEqual([json.loads(line) for line in text.splitlines()], [first, second])
            self.assertEqual(first, before)


if __name__ == "__main__":
    unittest.main()
