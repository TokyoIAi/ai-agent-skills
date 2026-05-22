"""Smoke tests for v0.8.5 session health policy and timestamp helpers.

Run from ``skill/origin-plot/``:

    py scripts\\test_session_health_logic.py
"""
from __future__ import annotations

import re
import sys
import traceback
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from origin_session_utils import (  # noqa: E402
    coerce_health_policy,
    health_defaults,
    merge_session_settings,
    session_defaults,
)
from origin_plot_from_config import current_timestamp_utc  # noqa: E402

ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_timestamp_format() -> None:
    ts = current_timestamp_utc()
    assert_true(
        bool(ISO_RE.match(ts)),
        f"timestamp_utc must match YYYY-MM-DDTHH:MM:SSZ, got {ts!r}",
    )


def test_health_defaults_present() -> None:
    defaults = session_defaults()
    health = defaults.get("health")
    assert_true(isinstance(health, dict), "session_defaults must include a health dict")
    expected = health_defaults()
    for key, value in expected.items():
        assert_true(
            health.get(key) == value,
            f"default health.{key} should be {value}, got {health.get(key)}",
        )


def test_health_merge_priority() -> None:
    profile = {"health": {"recent_window": 10}}
    explicit = {"health": {"degraded_ok_after_retry_threshold": 5}}
    cli = {"health": {"degraded_failed_threshold": 2, "recent_window": 50}}
    merged = merge_session_settings(profile, explicit, cli)
    health = merged["health"]
    assert_true(health["recent_window"] == 50, "CLI should override profile recent_window")
    assert_true(
        health["degraded_ok_after_retry_threshold"] == 5,
        "explicit should override default ok_after_retry threshold",
    )
    assert_true(
        health["degraded_failed_threshold"] == 2,
        "CLI should override default failed threshold",
    )


def test_health_validation_rejects_bad_values() -> None:
    bad_inputs = [
        {"health": {"recent_window": -1}},
        {"health": {"recent_window": 100000}},
        {"health": {"recent_window": "abc"}},
        {"health": {"degraded_ok_after_retry_threshold": -1}},
        {"health": {"degraded_failed_threshold": "one"}},
    ]
    for payload in bad_inputs:
        try:
            merge_session_settings(None, payload, None)
        except ValueError:
            continue
        raise AssertionError(f"merge should have rejected {payload!r}")


def _evaluate_health(recent_failed: int, recent_ok_after_retry: int, policy: dict) -> str:
    if recent_failed >= policy["degraded_failed_threshold"]:
        return "degraded"
    if recent_ok_after_retry >= policy["degraded_ok_after_retry_threshold"]:
        return "degraded"
    return "ok"


def test_health_status_rules() -> None:
    policy = health_defaults()
    assert_true(_evaluate_health(0, 0, policy) == "ok", "all-zero should be ok")
    assert_true(
        _evaluate_health(0, policy["degraded_ok_after_retry_threshold"], policy) == "degraded",
        "ok_after_retry at threshold should be degraded",
    )
    assert_true(
        _evaluate_health(policy["degraded_failed_threshold"], 0, policy) == "degraded",
        "failed at threshold should be degraded",
    )
    assert_true(
        _evaluate_health(0, policy["degraded_ok_after_retry_threshold"] - 1, policy) == "ok",
        "ok_after_retry below threshold should remain ok",
    )


def run_all() -> int:
    tests = [
        test_timestamp_format,
        test_health_defaults_present,
        test_health_merge_priority,
        test_health_validation_rejects_bad_values,
        test_health_status_rules,
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
    print("PASS: session health logic smoke tests ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_all())
