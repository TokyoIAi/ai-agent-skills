"""Run all smoke tests in sequence and report aggregate result.

Run from ``skill/origin-plot/``:

    py scripts\\run_smoke_tests.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TESTS = [
    ("test_session_retry_logic", [sys.executable, "scripts/test_session_retry_logic.py"]),
    ("test_cli_retry_injection", [sys.executable, "scripts/test_cli_retry_injection.py"]),
]


def main() -> int:
    results: list[tuple[str, bool]] = []
    for name, cmd in TESTS:
        print(f"--- {name} ---")
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=False)
        passed = result.returncode == 0
        results.append((name, passed))
        print()

    failed = [name for name, passed in results if not passed]
    if failed:
        print(f"FAIL: {len(failed)} smoke test(s) failed: {', '.join(failed)}")
        return 1
    print("PASS: all smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
