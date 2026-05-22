"""origin-plot v1.0 batch entry point.

Reads a small batch YAML and runs ``workflows/run_plot.py`` per job. A failed
job never prevents the report from being written. The verified v0.8.7 batch
script (``scripts/origin_batch_plot.py``) is still available for production
use; this thin wrapper shows the v1.0 surface the README documents.

Usage (from ``skill/origin-plot/``)::

    py workflows\\run_batch.py --batch-config configs\\examples\\batch.yaml
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.paths import current_timestamp_utc, rel, resolve_project_path  # noqa: E402
from core.report_writer import write_run_report  # noqa: E402

PASS_STATUSES = {"PASS", "PASS with warnings", "PASS with session_retry"}
BATCH_REPORT_PATH = PROJECT_ROOT / "reports" / "report_package" / "batch_report.json"


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise RuntimeError("Please install PyYAML: py -m pip install pyyaml") from exc
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"batch config must be a YAML mapping: {rel(path)}")
    return data


def run_single_plot(config_path: Path) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "workflows/run_plot.py",
        "--config",
        rel(config_path).replace("\\", "/"),
    ]
    completed = subprocess.run(
        cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, check=False
    )
    summary_path = PROJECT_ROOT / "reports" / "report_package" / "run_report.json"
    summary: dict[str, Any] | None = None
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            summary = None
    return {
        "command": cmd,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run multiple plot configs through the v1.0 core layer.")
    parser.add_argument("--batch-config", required=True, help="Batch YAML config (relative path).")
    args = parser.parse_args()

    batch_path = resolve_project_path(args.batch_config)
    if not batch_path.exists():
        print(f"FAIL: batch config not found: {rel(batch_path)}")
        return 1

    batch = load_yaml(batch_path)
    jobs = batch.get("jobs") or []
    if not isinstance(jobs, list) or not jobs:
        print("FAIL: batch config must define a non-empty jobs list")
        return 1

    report: dict[str, Any] = {
        "timestamp_utc": current_timestamp_utc(),
        "status": "PASS",
        "batch_config": rel(batch_path),
        "batch_name": batch.get("batch_name") or batch_path.stem,
        "continue_on_error": bool(batch.get("continue_on_error", True)),
        "job_count": len(jobs),
        "passed_count": 0,
        "failed_count": 0,
        "jobs": [],
        "warnings": [],
        "errors": [],
    }

    for index, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            report["errors"].append(f"job #{index} is not a mapping")
            report["failed_count"] += 1
            if not report["continue_on_error"]:
                break
            continue
        name = str(job.get("name") or f"job_{index}")
        config_value = job.get("config")
        if not config_value:
            report["jobs"].append({"name": name, "status": "FAIL", "error": "missing config"})
            report["failed_count"] += 1
            if not report["continue_on_error"]:
                break
            continue

        config_path = resolve_project_path(str(config_value))
        if not config_path.exists():
            report["jobs"].append({
                "name": name,
                "config": rel(config_path),
                "status": "FAIL",
                "error": "config not found",
            })
            report["failed_count"] += 1
            if not report["continue_on_error"]:
                break
            continue

        print(f"--- batch job {name} ({rel(config_path)}) ---")
        run = run_single_plot(config_path)
        if run["stdout"]:
            sys.stdout.write(run["stdout"])
        summary = run["summary"] or {}
        job_status = summary.get("status") or ("FAIL" if run["returncode"] != 0 else "UNKNOWN")
        is_pass = run["returncode"] == 0 and job_status in PASS_STATUSES
        report["jobs"].append({
            "name": name,
            "config": rel(config_path),
            "status": job_status,
            "exit_code": run["returncode"],
            "outputs": summary.get("outputs") or {},
            "report_package": (summary.get("report_package") or {}).get("package_dir"),
        })
        if is_pass:
            report["passed_count"] += 1
        else:
            report["failed_count"] += 1
            if not report["continue_on_error"]:
                break

    if report["failed_count"] and report["passed_count"]:
        report["status"] = "PARTIAL PASS"
    elif report["failed_count"] and not report["passed_count"]:
        report["status"] = "FAIL"

    write_run_report(BATCH_REPORT_PATH, report)
    print(f"batch status: {report['status']} ({report['passed_count']}/{report['job_count']})")
    print(f"batch report: {rel(BATCH_REPORT_PATH)}")
    return 0 if report["status"] in {"PASS", "PARTIAL PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
