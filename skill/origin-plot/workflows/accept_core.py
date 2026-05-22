"""Minimal acceptance suite for the v1.0 core surface.

Runs ``run_plot.py`` against the three example configs, confirms PNG/PDF/OPJU
existence, scans ``reports/`` for absolute path leaks via the legacy hygiene
script, and prints ``PASS: origin-plot core acceptance ok`` on success.

Usage (from ``skill/origin-plot/``)::

    py workflows\\accept_core.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.paths import current_timestamp_utc, rel  # noqa: E402

EXAMPLE_CONFIGS = [
    "configs/examples/line_plot.yaml",
    "configs/examples/errorbar_plot.yaml",
    "configs/examples/fitting_plot.yaml",
]

REPORT_PACKAGE_RUN_REPORT = PROJECT_ROOT / "reports" / "report_package" / "run_report.json"
ACCEPT_REPORT_PATH = PROJECT_ROOT / "reports" / "report_package" / "accept_core_report.json"


def run_plot(config: str) -> dict[str, Any]:
    cmd = [sys.executable, "workflows/run_plot.py", "--config", config]
    completed = subprocess.run(
        cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, check=False
    )
    summary: dict[str, Any] | None = None
    if REPORT_PACKAGE_RUN_REPORT.exists():
        try:
            summary = json.loads(REPORT_PACKAGE_RUN_REPORT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            summary = None
    return {
        "config": config,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "summary": summary,
    }


def has_all_outputs(summary: dict[str, Any] | None) -> bool:
    if not summary:
        return False
    outputs = summary.get("outputs") or {}
    return all((info or {}).get("exists") for info in outputs.values()) if outputs else False


def main() -> int:
    accept_report: dict[str, Any] = {
        "timestamp_utc": current_timestamp_utc(),
        "status": "PASS",
        "examples": [],
        "hygiene": None,
        "warnings": [],
        "errors": [],
    }

    pass_statuses = {"PASS", "PASS with warnings", "PASS with session_retry"}

    for config in EXAMPLE_CONFIGS:
        print(f"--- accepting {config} ---")
        run = run_plot(config)
        if run["stdout"]:
            sys.stdout.write(run["stdout"])
        if run["stderr"] and run["exit_code"] != 0:
            sys.stderr.write(run["stderr"])
        summary = run["summary"] or {}
        status = summary.get("status") or ("FAIL" if run["exit_code"] != 0 else "UNKNOWN")
        outputs_ok = has_all_outputs(summary)
        accept_report["examples"].append({
            "config": config,
            "exit_code": run["exit_code"],
            "status": status,
            "outputs_ok": outputs_ok,
            "outputs": summary.get("outputs"),
            "report_package": (summary.get("report_package") or {}).get("package_dir"),
        })
        if not (run["exit_code"] == 0 and status in pass_statuses and outputs_ok):
            accept_report["status"] = "FAIL"
            accept_report["errors"].append(
                f"example {config} did not pass: exit={run['exit_code']} status={status} outputs_ok={outputs_ok}"
            )

    print("--- hygiene scan ---")
    hygiene = subprocess.run(
        [sys.executable, "ops/hygiene/check_committed_reports.py"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True, check=False,
    )
    sys.stdout.write(hygiene.stdout)
    if hygiene.returncode != 0:
        sys.stderr.write(hygiene.stderr)
        accept_report["status"] = "FAIL"
        accept_report["errors"].append("path leak scan failed")
    accept_report["hygiene"] = {
        "exit_code": hygiene.returncode,
        "stdout_tail": hygiene.stdout.strip().splitlines()[-1] if hygiene.stdout else "",
    }

    ACCEPT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACCEPT_REPORT_PATH.write_text(
        json.dumps(accept_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"accept_core report: {rel(ACCEPT_REPORT_PATH)}")
    if accept_report["status"] == "PASS":
        print("PASS: origin-plot core acceptance ok")
        return 0
    print(f"FAIL: origin-plot core acceptance ({accept_report['status']})")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
