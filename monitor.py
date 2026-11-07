import argparse
import json
import math
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


def check_once(url, timeout):
    started = time.perf_counter()
    try:
        with urlopen(url, timeout=timeout) as response:
            finished = time.perf_counter()
            elapsed_ms = (finished - started) * 1000

            return {
                "status_code": response.status,
                "elapsed_ms": elapsed_ms,
                "url": url,
                "ok": 200 <= response.status < 300,
                "error": None,
            }
    except HTTPError as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        status_code = exc.code
        error = str(exc.reason)
        exc.close()
        return {
            "status_code": status_code,
            "elapsed_ms": elapsed_ms,
            "url": url,
            "ok": False,
            "error": error,
        }
    except URLError as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {
            "status_code": None,
            "elapsed_ms": elapsed_ms,
            "url": url,
            "ok": False,
            "error": str(exc.reason),
        }
    except OSError as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {
            "status_code": None,
            "elapsed_ms": elapsed_ms,
            "url": url,
            "ok": False,
            "error": str(exc) or type(exc).__name__,
        }


def availability_percent(checks):
    if not checks:
        return None
    successful = 0
    for result in checks:
        if result["ok"]:
            successful += 1
    return successful / len(checks) * 100


def append_result(path, result):
    with Path(path).open("a", encoding="utf-8") as file:
        file.write(json.dumps(result, ensure_ascii=False) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="HTTP-монитор")
    parser.add_argument("--url", default="http://127.0.0.1:8765/health")
    parser.add_argument("--timeout", type=float, default=0.5)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("timeout должен быть положительным конечным числом")
    if not math.isfinite(args.interval) or args.interval < 0:
        parser.error("interval должен быть неотрицательным конечным числом")
    if args.count <= 0:
        parser.error("count должен быть положительным")
    try:
        parsed_url = urlsplit(args.url)
    except ValueError:
        parser.error("Некорректный URL")
    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        parser.error("Нужен полный HTTP/HTTPS URL")
    checks = []
    for index in range(args.count):
        result = check_once(args.url, args.timeout)
        checks.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if args.out:
            append_result(args.out, result)
        if index + 1 < args.count:
            time.sleep(args.interval)
    print(
        json.dumps(
            {
                "type": "summary",
                "total": len(checks),
                "availability_percent": availability_percent(checks),
            }
        )
    )
    return 0 if all(result["ok"] for result in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
