"""CLI retry injection smoke test.

Invokes ``origin_plot_from_config.py`` with ``--inject-session-error-once`` via
subprocess and verifies the retry path works end-to-end through the CLI route.

Run from ``skill/origin-plot/``:

    py scripts\\test_cli_retry_injection.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "origin_plot_v0_2_report.json"
CONFIG = "configs/fitting/linear_fit_config.yaml"
OUTPUT_DIR = PROJECT_ROOT / "output" / "origin_plot_fitting"


def run() -> int:
    cmd = [
        sys.executable,
        "scripts/origin_plot_from_config.py",
        "--config", CONFIG,
        "--inject-session-error-once",
        "--session-max-retries", "1",
        "--session-retry-delay-seconds", "1",
        "--no-kill-stale-origin-before-retry",
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"FAIL: exit code {result.returncode}")
        print(result.stdout[-2000:] if result.stdout else "")
        print(result.stderr[-2000:] if result.stderr else "")
        return 1

    if not REPORT_PATH.exists():
        print(f"FAIL: report not found at {REPORT_PATH}")
        return 1

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []

    status = report.get("status")
    if status != "PASS with session_retry":
        errors.append(f"status={status!r}, expected 'PASS with session_retry'")

    session = report.get("origin_session") or {}
    if not session.get("retry_used"):
        errors.append("origin_session.retry_used is not true")
    if session.get("attempts") != 2:
        errors.append(f"origin_session.attempts={session.get('attempts')}, expected 2")
    if not session.get("injection_triggered"):
        errors.append("origin_session.injection_triggered is not true")
    if session.get("final_session_status") != "ok_after_retry":
        errors.append(f"final_session_status={session.get('final_session_status')!r}")
    cli_overrides = session.get("cli_session_overrides") or {}
    if not cli_overrides:
        errors.append("cli_session_overrides is empty")

    # Verify outputs exist.
    basename = report.get("outputs", {})
    for key in ("png", "pdf", "opju"):
        info = (report.get("outputs") or {}).get(key) or {}
        if not info.get("exists"):
            errors.append(f"output {key} does not exist")

    if errors:
        for err in errors:
            print(f"FAIL: {err}")
        return 1

    print("PASS: CLI retry injection smoke test ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
