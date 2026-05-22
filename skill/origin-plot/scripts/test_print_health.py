"""Smoke test for the --print-health helper format.

Run from ``skill/origin-plot/``:

    py scripts\\test_print_health.py

This test does not call Origin. It validates the ``emit_health_snapshot_line``
contract by running the function in a subprocess-free manner (capturing stdout)
and checking the prefix and JSON shape.
"""
from __future__ import annotations

import io
import json
import sys
import traceback
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from origin_plot_from_config import emit_health_snapshot_line  # noqa: E402

PREFIX = "HEALTH_SNAPSHOT_JSON: "


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def capture_emit(report: dict) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        emit_health_snapshot_line(report)
    return buf.getvalue().strip()


def test_emit_with_full_snapshot() -> None:
    report = {
        "session_health_snapshot": {
            "history_path": "reports/session_history.json",
            "entries_seen": 3,
            "recent_window": 20,
            "degraded_ok_after_retry_threshold": 3,
            "degraded_failed_threshold": 1,
            "recent_ok": 3,
            "recent_ok_after_retry": 0,
            "recent_failed": 0,
            "recent_injection_triggered": 0,
            "health_status": "ok",
        }
    }
    line = capture_emit(report)
    assert_true(
        line.startswith(PREFIX),
        f"line must start with prefix {PREFIX!r}; got {line!r}",
    )
    payload = line[len(PREFIX):]
    parsed = json.loads(payload)
    assert_true(parsed.get("health_status") == "ok", f"expected health_status=ok; got {parsed!r}")
    assert_true(
        parsed.get("entries_seen") == 3,
        f"expected entries_seen=3; got {parsed!r}",
    )


def test_emit_with_missing_snapshot() -> None:
    line = capture_emit({})
    assert_true(line.startswith(PREFIX), f"line must start with prefix; got {line!r}")
    parsed = json.loads(line[len(PREFIX):])
    assert_true(
        parsed.get("health_status") == "unknown",
        f"missing snapshot must produce health_status=unknown; got {parsed!r}",
    )


def test_emit_payload_has_no_absolute_paths() -> None:
    report = {
        "session_health_snapshot": {
            "history_path": "reports/session_history.json",
            "health_status": "degraded",
        }
    }
    line = capture_emit(report)
    payload = line[len(PREFIX):]
    forbidden = ("H:\\", "C:\\", "E:\\", "/mnt/")
    for marker in forbidden:
        assert_true(
            marker not in payload,
            f"payload must not contain {marker!r}; got {payload!r}",
        )


def run_all() -> int:
    tests = [
        test_emit_with_full_snapshot,
        test_emit_with_missing_snapshot,
        test_emit_payload_has_no_absolute_paths,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"ok: {test.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL: {test.__name__}: {exc}")
        except Exception:  # noqa: BLE001
            failed += 1
            print(f"FAIL: {test.__name__} raised an unexpected error")
            traceback.print_exc()
    if failed:
        print(f"FAIL: {failed} test(s) failed")
        return 1
    print("PASS: print health smoke tests ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_all())
