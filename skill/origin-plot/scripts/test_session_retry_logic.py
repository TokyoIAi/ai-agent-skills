"""Smoke tests for v0.8.2 session retry helpers. No Origin dependency.

Run from ``skill/origin-plot/``:

    py scripts\\test_session_retry_logic.py

The test exits non-zero on any assertion failure and prints diagnostic context.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

# Allow imports relative to this script.
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from origin_session_utils import (  # noqa: E402
    InjectedSessionError,
    is_session_error,
    make_injected_session_error,
    merge_session_settings,
    session_defaults,
)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_classifier_recognizes_session_errors() -> None:
    cases = [
        RuntimeError("OriginExt::ApplicationBase::LT_execute ==> ill state"),
        RuntimeError("Exception in OriginExt set_show failed"),
        RuntimeError("invalid pointer (\u65e0\u6548\u6307\u9488)"),
        RuntimeError("originpro could not start"),
        RuntimeError("ApplicationBase_LT_execute returned bad result"),
        type("COMError", (Exception,), {})("call failed"),
        make_injected_session_error(),
    ]
    for exc in cases:
        assert_true(
            is_session_error(exc),
            f"expected session-error classification for: {type(exc).__name__}: {exc}",
        )


def test_classifier_ignores_non_session_errors() -> None:
    cases = [
        FileNotFoundError("input_file does not exist: data/missing.csv"),
        ValueError("Selected x/y columns must contain at least 2 valid numeric rows."),
        KeyError("y_columns"),
        TypeError("y_error_columns must be a mapping"),
    ]
    for exc in cases:
        assert_true(
            not is_session_error(exc),
            f"unexpected session-error classification for: {type(exc).__name__}: {exc}",
        )


def test_merge_priority_profile_explicit_cli() -> None:
    profile = {
        "retry_on_com_error": True,
        "max_retries": 1,
        "kill_stale_origin_before_retry": True,
        "retry_delay_seconds": 2.0,
        "inject_session_error_once": False,
    }
    explicit = {
        "max_retries": 2,
        "retry_delay_seconds": 1.5,
    }
    cli_overrides = {
        "max_retries": 3,
        "kill_stale_origin_before_retry": False,
    }

    merged_profile_only = merge_session_settings(profile, None, None)
    assert_true(merged_profile_only["max_retries"] == 1, "profile not respected")
    assert_true(merged_profile_only["kill_stale_origin_before_retry"] is True, "profile bool not respected")

    merged_with_explicit = merge_session_settings(profile, explicit, None)
    assert_true(merged_with_explicit["max_retries"] == 2, "explicit should override profile")
    assert_true(merged_with_explicit["retry_delay_seconds"] == 1.5, "explicit should override delay")
    assert_true(merged_with_explicit["kill_stale_origin_before_retry"] is True, "explicit absent => profile preserved")

    merged_with_cli = merge_session_settings(profile, explicit, cli_overrides)
    assert_true(merged_with_cli["max_retries"] == 3, "CLI should override explicit")
    assert_true(merged_with_cli["kill_stale_origin_before_retry"] is False, "CLI should override profile")
    assert_true(merged_with_cli["retry_delay_seconds"] == 1.5, "CLI absent => explicit preserved")
    assert_true(
        merged_with_cli["inject_session_error_once"] is False,
        "injection default must remain False without explicit/CLI request",
    )


def test_merge_uses_defaults_when_inputs_empty() -> None:
    merged = merge_session_settings(None, None, None)
    defaults = session_defaults()
    for key, value in defaults.items():
        assert_true(merged[key] == value, f"default mismatch for {key}: {merged[key]} != {value}")


def test_merge_rejects_invalid_values() -> None:
    bad_inputs = [
        ({"max_retries": -1}, "max_retries below range"),
        ({"max_retries": 6}, "max_retries above range"),
        ({"retry_delay_seconds": -0.5}, "retry_delay_seconds below range"),
        ({"retry_delay_seconds": 999}, "retry_delay_seconds above range"),
        ({"retry_on_com_error": "yes"}, "retry_on_com_error wrong type"),
        ({"inject_session_error_once": 1}, "inject_session_error_once wrong type"),
        ({"history_max_entries": -5}, "history_max_entries below range"),
        ({"history_max_entries": 999999}, "history_max_entries above range"),
        ({"history_max_entries": "abc"}, "history_max_entries wrong type"),
    ]
    for payload, description in bad_inputs:
        try:
            merge_session_settings(None, payload, None)
        except ValueError:
            continue
        raise AssertionError(f"merge should have rejected {description}: {payload!r}")


def test_history_max_entries_default_and_fallback() -> None:
    # Default should be 100.
    merged = merge_session_settings(None, None, None)
    assert_true(
        merged["history_max_entries"] == 100,
        f"default history_max_entries should be 100, got {merged.get('history_max_entries')}",
    )
    # None or 0 should fall back to 100 silently.
    fallback_none = merge_session_settings(None, {"history_max_entries": None}, None)
    assert_true(
        fallback_none["history_max_entries"] == 100,
        f"history_max_entries=None should fall back to 100, got {fallback_none['history_max_entries']}",
    )
    fallback_zero = merge_session_settings(None, {"history_max_entries": 0}, None)
    assert_true(
        fallback_zero["history_max_entries"] == 100,
        f"history_max_entries=0 should fall back to 100, got {fallback_zero['history_max_entries']}",
    )


def test_history_max_entries_priority() -> None:
    profile = {"history_max_entries": 50}
    explicit = {"history_max_entries": 75}
    cli = {"history_max_entries": 200}

    merged_profile = merge_session_settings(profile, None, None)
    assert_true(
        merged_profile["history_max_entries"] == 50,
        "profile history_max_entries not honored",
    )
    merged_explicit = merge_session_settings(profile, explicit, None)
    assert_true(
        merged_explicit["history_max_entries"] == 75,
        "explicit history_max_entries should override profile",
    )
    merged_cli = merge_session_settings(profile, explicit, cli)
    assert_true(
        merged_cli["history_max_entries"] == 200,
        "CLI history_max_entries should override explicit and profile",
    )


def run_all() -> int:
    tests = [
        test_classifier_recognizes_session_errors,
        test_classifier_ignores_non_session_errors,
        test_merge_priority_profile_explicit_cli,
        test_merge_uses_defaults_when_inputs_empty,
        test_merge_rejects_invalid_values,
        test_history_max_entries_default_and_fallback,
        test_history_max_entries_priority,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"ok: {test.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL: {test.__name__}: {exc}")
        except Exception:  # noqa: BLE001 - report unexpected errors clearly
            failed += 1
            print(f"FAIL: {test.__name__} raised an unexpected error")
            traceback.print_exc()
    if failed:
        print(f"FAIL: {failed} test(s) failed")
        return 1
    print("PASS: session retry logic smoke tests ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_all())
