from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SINGLE_REPORT_PATH = PROJECT_ROOT / "reports" / "origin_plot_v0_2_report.json"
BATCH_REPORT_PATH = PROJECT_ROOT / "reports" / "origin_plot_v0_3_batch_report.json"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ModuleNotFoundError:
        raise RuntimeError("Please install PyYAML: py -m pip install pyyaml") from None

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError("Batch config must be a YAML mapping.")
    return data


def check_batch_config(batch: dict[str, Any]) -> list[dict[str, str]]:
    if not batch.get("batch_name"):
        raise ValueError("batch_name is required.")
    jobs = batch.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("jobs must be a non-empty list.")

    checked: list[dict[str, str]] = []
    for index, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            raise ValueError(f"Job {index} must be a mapping.")
        name = job.get("name")
        config = job.get("config")
        if not name or not config:
            raise ValueError(f"Job {index} must include name and config.")
        config_path = resolve_project_path(str(config))
        if not config_path.exists():
            raise FileNotFoundError(f"Job {name} config does not exist: {rel(config_path)}")
        checked.append({"name": str(name), "config": rel(config_path)})
    return checked


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def empty_outputs() -> dict[str, dict[str, Any]]:
    return {
        "png": {"path": None, "exists": False, "size_bytes": 0},
        "pdf": {"path": None, "exists": False, "size_bytes": 0},
        "opju": {"path": None, "exists": False, "size_bytes": 0},
    }


def sanitize_error(text: str) -> str:
    if not text:
        return ""
    sanitized = text.replace(str(PROJECT_ROOT), ".")
    sanitized = sanitized.replace(str(PROJECT_ROOT).replace("\\", "\\\\"), ".")
    return sanitized[-4000:]


def read_single_report() -> dict[str, Any] | None:
    if not SINGLE_REPORT_PATH.exists():
        return None
    try:
        return json.loads(SINGLE_REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def job_from_single_report(name: str, config: str, report: dict[str, Any]) -> dict[str, Any]:
    status = "PASS" if report.get("status") == "PASS" else "FAIL"
    return {
        "name": name,
        "config": config,
        "status": status,
        "outputs": report.get("outputs") or empty_outputs(),
        "warnings": report.get("warnings", []),
        "error": None if status == "PASS" else "; ".join(report.get("errors") or ["plot failed"]),
    }


def run_job(job: dict[str, str]) -> dict[str, Any]:
    name = job["name"]
    config = job["config"]

    validation = run_command(
        [sys.executable, "scripts/validate_origin_plot_config.py", "--config", config]
    )
    if validation.returncode != 0:
        return {
            "name": name,
            "config": config,
            "status": "FAIL",
            "outputs": empty_outputs(),
            "warnings": [],
            "error": "validation failed: " + sanitize_error(validation.stdout + validation.stderr),
        }

    plotting = run_command(
        [sys.executable, "scripts/origin_plot_from_config.py", "--config", config]
    )
    single_report = read_single_report()
    if single_report is not None:
        result = job_from_single_report(name, config, single_report)
        if plotting.returncode != 0 and result["status"] == "PASS":
            result["status"] = "FAIL"
            result["error"] = "plot command failed despite PASS report"
        if plotting.returncode != 0 and not result["error"]:
            result["error"] = sanitize_error(plotting.stdout + plotting.stderr)
        return result

    return {
        "name": name,
        "config": config,
        "status": "FAIL",
        "outputs": empty_outputs(),
        "warnings": [],
        "error": "plot failed and no single-job report was generated: "
        + sanitize_error(plotting.stdout + plotting.stderr),
    }


def batch_status(passed_count: int, failed_count: int) -> str:
    if passed_count > 0 and failed_count == 0:
        return "PASS"
    if passed_count > 0 and failed_count > 0:
        return "PARTIAL PASS"
    return "FAIL"


def save_batch_report(report: dict[str, Any]) -> None:
    BATCH_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    BATCH_REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def restore_single_report(original_text: str | None) -> None:
    if original_text is None:
        return
    SINGLE_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SINGLE_REPORT_PATH.write_text(original_text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run origin-plot v0.3 batch plotting.")
    parser.add_argument("--batch-config", default="configs/batch/batch_plot_config.yaml")
    args = parser.parse_args()

    batch_config_path = resolve_project_path(args.batch_config)
    original_single_report = (
        SINGLE_REPORT_PATH.read_text(encoding="utf-8") if SINGLE_REPORT_PATH.exists() else None
    )
    results: list[dict[str, Any]] = []
    batch_name = None
    continue_on_error = True

    try:
        if not batch_config_path.exists():
            raise FileNotFoundError(f"Batch config does not exist: {rel(batch_config_path)}")
        batch = load_yaml(batch_config_path)
        batch_name = str(batch["batch_name"])
        continue_on_error = bool(batch.get("continue_on_error", True))
        jobs = check_batch_config(batch)

        for job in jobs:
            print(f"Running job: {job['name']} ({job['config']})")
            result = run_job(job)
            results.append(result)
            print(f"- {job['name']}: {result['status']}")
            if result["status"] != "PASS" and not continue_on_error:
                break

    except Exception as exc:  # noqa: BLE001 - batch must always write a report
        results.append(
            {
                "name": "__batch_setup__",
                "config": rel(batch_config_path),
                "status": "FAIL",
                "outputs": empty_outputs(),
                "warnings": [],
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        if batch_name is None:
            batch_name = batch_config_path.stem

    passed_count = sum(1 for job in results if job.get("status") == "PASS")
    failed_count = sum(1 for job in results if job.get("status") != "PASS")
    status = batch_status(passed_count, failed_count)
    report = {
        "status": status,
        "batch_name": batch_name,
        "job_count": len(results),
        "passed_count": passed_count,
        "failed_count": failed_count,
        "continue_on_error": continue_on_error,
        "jobs": results,
        "manual_intervention": {
            "policy": "GUI dialog auto-clicking is intentionally not implemented.",
            "first_run_origin_dialog_caveat": True,
        },
    }
    save_batch_report(report)
    restore_single_report(original_single_report)

    print(f"batch_name: {batch_name}")
    print(f"job_count: {len(results)}")
    print(f"passed_count: {passed_count}")
    print(f"failed_count: {failed_count}")
    print(f"report path: {rel(BATCH_REPORT_PATH)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
