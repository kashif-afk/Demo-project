"""Small local web page that runs the real settlement code. Used by the Playwright tests and the Loom demo.

Synthetic data, in-memory state, Python standard library only.
Run: python src/app.py   then open http://127.0.0.1:8000
"""

import importlib
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ledger import CREDITS_PER_TASK, Ledger, SimulatedCrash
from notifier import MockNotifier
from window import in_window, parse_utc, settlement_window

RUN_AT = datetime(2026, 10, 27, 9, 0, tzinfo=timezone.utc)  # Tuesday 09:00 UTC
SAMPLE_TASKS = [
    {"task_id": "T-1", "user_id": "U-1", "status": "completed", "completed_at": "2026-10-19T00:00:00Z"},
    {"task_id": "T-2", "user_id": "U-2", "status": "completed", "completed_at": "2026-10-21T12:30:00Z"},
    {"task_id": "T-3", "user_id": "U-3", "status": "completed", "completed_at": "2026-10-26T04:59:00+05:00"},
    {"task_id": "T-4", "user_id": "U-1", "status": "completed", "completed_at": "2026-10-23T16:45:00Z"},
    {"task_id": "T-5", "user_id": "U-2", "status": "completed", "completed_at": "2026-10-26T00:00:00Z"},
    {"task_id": "T-6", "user_id": "U-3", "status": "completed", "completed_at": "2026-10-26T05:00:00+05:00"},
]
DUPLICATE = SAMPLE_TASKS[1]  # "T-2 sent twice" appends this row to the input
PAGE = Path(__file__).with_name("index.html")


def qualifies(task: dict) -> bool:
    start, end = settlement_window(RUN_AT)
    return task["status"] == "completed" and in_window(parse_utc(task["completed_at"]), start, end)


class Demo:
    def __init__(self):
        self.reset("faulty")

    def reset(self, version: str) -> None:
        if version not in ("faulty", "fixed"):
            raise ValueError(f"unknown version: {version!r}")
        self.version = version
        self.ledger = Ledger()
        self.notifier = MockNotifier()
        self.runs: list[dict] = []

    def run(self, crash_after: int | None, notifications_down: bool, duplicate_input: bool = False) -> None:
        settle = importlib.import_module(f"settle_{self.version}").settle
        self.notifier.fail = notifications_down
        tasks = SAMPLE_TASKS + [DUPLICATE] if duplicate_input else SAMPLE_TASKS
        try:
            result = settle(tasks, RUN_AT, self.ledger, self.notifier, crash_after=crash_after)
        except SimulatedCrash as crash:
            self.runs.append({"crashed": str(crash)})
            return
        self.runs.append({key: result[key] for key in ("paid", "duplicate_input", "already_paid", "notify_failed")})

    def state(self) -> dict:
        start, end = settlement_window(RUN_AT)
        qualifying = [t["task_id"] for t in SAMPLE_TASKS if qualifies(t)]
        times_paid = {t["task_id"]: self.ledger.times_paid(t["task_id"]) for t in SAMPLE_TASKS}
        return {
            "version": self.version,
            "run_at": RUN_AT.isoformat(),
            "window": [start.isoformat(), end.isoformat()],
            "tasks": [dict(t, qualifies=qualifies(t)) for t in SAMPLE_TASKS],
            "payouts": [{"task_id": p.task_id, "user_id": p.user_id, "amount": p.amount} for p in self.ledger.payouts],
            "total_paid": self.ledger.total(),
            "expected_total": CREDITS_PER_TASK * len(qualifying),
            "paid_more_than_once": [task_id for task_id, n in times_paid.items() if n > 1],
            "notified": self.notifier.sent,
            "runs": self.runs,
        }


demo = Demo()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/state":
            self._json(demo.state())
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        try:
            if self.path == "/api/reset":
                demo.reset(body.get("version", demo.version))
            elif self.path == "/api/run":
                demo.run(body.get("crash_after"), bool(body.get("notifications_down")), bool(body.get("duplicate_input")))
            else:
                return self._send(404, b"not found", "text/plain")
        except ValueError as error:
            return self._json({"error": str(error)}, status=400)
        self._json(demo.state())

    def _json(self, data: dict, status: int = 200) -> None:
        self._send(status, json.dumps(data).encode(), "application/json")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep test output quiet
        pass


def make_server(port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    server = make_server()
    print("Weekly reward payout demo: http://127.0.0.1:8000  (Ctrl+C to stop)")
    server.serve_forever()
