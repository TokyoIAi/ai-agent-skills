"""Run all smoke tests in sequence and report aggregate result.

Run from ``skill/origin-plot/``:

    py scripts\\run_smoke_tests.py
    py scripts\\run_smoke_tests.py --skip-origin
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def all_tests() -> list[tuple[str, list[str], bool]]:
    """Return (name, command, requires_origin) for each smoke test."""
    return [
        (
            "test_session_retry_logic",
            [sys.executable, "scripts/test_session_retry_logic.py"],
            False,
        ),
        (
            "test_session_health_logic",
            [sys.executable, "scripts/test_session_health_logic.py"],
            False,
        ),
        (
            "test_print_health",
            [sys.executable, "scripts/test_print_health.py"],
            False,
        ),
        (
            "test_smart_input_logic",
            [sys.executable, "scripts/test_smart_input_logic.py"],
            False,
        ),
        (
            "test_cli_retry_injection",
            [sys.executable, "scripts/test_cli_retry_injection.py"],
            True,
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run origin-plot smoke tests.")
    parser.add_argument(
        "--skip-origin",
        action="store_true",
        help="Skip smoke tests that require a working Origin install.",
    )
    args = parser.parse_args()

    plan: list[tuple[str, list[str]]] = []
    for name, cmd, requires_origin in all_tests():
        if args.skip_origin and requires_origin:
            print(f"SKIP: {name} (requires Origin)")
            continue
        plan.append((name, cmd))

    if not plan:
        print("FAIL: no smoke tests to run with the given options")
        return 1

    results: list[tuple[str, int, float]] = []
    for name, cmd in plan:
        print(f"--- {name} ---")
        start = time.monotonic()
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=False)
        elapsed = time.monotonic() - start
        results.append((name, result.returncode, elapsed))
        print()

    print("--- summary ---")
    for name, rc, elapsed in results:
        verdict = "ok" if rc == 0 else "FAIL"
        print(f"{verdict}: {name} (exit={rc}, {elapsed:.2f}s)")

    failed = [name for name, rc, _ in results if rc != 0]
    if failed:
        print(f"FAIL: {len(failed)} smoke test(s) failed: {', '.join(failed)}")
        return 1
    print("PASS: all smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
