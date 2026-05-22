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
RETRY_CONFIG_PATH = PROJECT_ROOT / "configs" / "generated" / "retry_failed_jobs.yaml"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def current_timestamp_utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    report_status = str(report.get("status"))
    status = report_status if report_status in {"PASS", "PASS with warnings", "PASS with session_retry"} else "FAIL"
    style = report.get("style") or {}
    errorbar = report.get("errorbar") or {}
    fitting = report.get("fitting") or {}
    fitting_annotation = report.get("fitting_annotation") or {}
    fitting_summary_csv = report.get("fitting_summary_csv") or {}
    residuals = report.get("residuals") or {}
    origin_session = report.get("origin_session") or {}
    return {
        "name": name,
        "config": config,
        "status": status,
        "outputs": report.get("outputs") or empty_outputs(),
        "warnings": report.get("warnings", []),
        "style": style,
        "style_warnings": style.get("style_warnings", []),
        "errorbar": errorbar,
        "fitting": fitting,
        "fitting_annotation": fitting_annotation,
        "fitting_summary_csv": fitting_summary_csv,
        "residuals": residuals,
        "origin_session": origin_session,
        "error": None
        if status in {"PASS", "PASS with warnings", "PASS with session_retry"}
        else "; ".join(report.get("errors") or ["plot failed"]),
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


def is_job_pass(job: dict[str, Any]) -> bool:
    return job.get("status") in {"PASS", "PASS with warnings", "PASS with session_retry"}


def save_batch_report(report: dict[str, Any]) -> None:
    BATCH_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    BATCH_REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def save_yaml(path: Path, data: dict[str, Any]) -> None:
    try:
        import yaml
    except ModuleNotFoundError:
        raise RuntimeError("Please install PyYAML: py -m pip install pyyaml") from None

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def create_retry_config(batch_name: str | None, results: list[dict[str, Any]]) -> dict[str, Any]:
    failed_jobs = [
        {"name": str(job["name"]), "config": str(job["config"])}
        for job in results
        if not is_job_pass(job) and job.get("name") != "__batch_setup__"
    ]
    retry_info = {
        "generated": False,
        "path": rel(RETRY_CONFIG_PATH),
        "failed_job_count": len(failed_jobs),
    }
    if not failed_jobs:
        return retry_info

    save_yaml(
        RETRY_CONFIG_PATH,
        {
            "batch_name": f"{batch_name or 'batch'}_retry_failed",
            "continue_on_error": True,
            "jobs": failed_jobs,
        },
    )
    retry_info["generated"] = True
    return retry_info


def style_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    style_profiles: list[str] = []
    jobs_with_warnings = 0
    for job in results:
        style = job.get("style") or {}
        profile = style.get("style_profile")
        if profile and profile not in style_profiles:
            style_profiles.append(profile)
        if job.get("style_warnings"):
            jobs_with_warnings += 1
    return {
        "jobs_with_style_warnings": jobs_with_warnings,
        "style_profiles_used": style_profiles,
    }


def errorbar_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    requested = 0
    applied = 0
    with_warnings = 0
    for job in results:
        errorbar = job.get("errorbar") or {}
        if errorbar.get("requested"):
            requested += 1
        if errorbar.get("applied"):
            applied += 1
        if errorbar.get("warnings"):
            with_warnings += 1
    return {
        "jobs_requesting_errorbar": requested,
        "jobs_errorbar_applied": applied,
        "jobs_errorbar_with_warnings": with_warnings,
    }


def fitting_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    requested = 0
    applied = 0
    with_warnings = 0
    models_used: list[str] = []
    for job in results:
        fitting = job.get("fitting") or {}
        if fitting.get("requested"):
            requested += 1
        if fitting.get("applied"):
            applied += 1
        if fitting.get("warnings"):
            with_warnings += 1
        for model in fitting.get("models") or []:
            model_name = model.get("model")
            if model_name and model_name not in models_used:
                models_used.append(str(model_name))
    return {
        "jobs_requesting_fitting": requested,
        "jobs_fitting_applied": applied,
        "jobs_fitting_with_warnings": with_warnings,
        "models_used": models_used,
    }


def fit_artifact_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    annotation_requested = 0
    annotation_applied = 0
    summary_csv_outputs: list[str] = []
    residual_csv_count = 0
    residual_plot_count = 0
    jobs_with_warnings = 0
    for job in results:
        annotation = job.get("fitting_annotation") or {}
        summary_csv = job.get("fitting_summary_csv") or {}
        residuals = job.get("residuals") or {}

        if annotation.get("requested"):
            annotation_requested += 1
        if annotation.get("applied"):
            annotation_applied += 1

        if summary_csv.get("requested"):
            csv_path = summary_csv.get("path")
            if csv_path and csv_path not in summary_csv_outputs:
                summary_csv_outputs.append(str(csv_path))

        for record in residuals.get("csv_outputs") or []:
            if record.get("exists"):
                residual_csv_count += 1
        for record in residuals.get("residual_plot_outputs") or []:
            if record.get("png_exists"):
                residual_plot_count += 1
            if record.get("pdf_exists"):
                residual_plot_count += 1

        if annotation.get("warnings") or summary_csv.get("warnings") or residuals.get("warnings"):
            jobs_with_warnings += 1

    return {
        "jobs_with_annotation_requested": annotation_requested,
        "jobs_with_annotation_applied": annotation_applied,
        "summary_csv_outputs": summary_csv_outputs,
        "residual_csv_count": residual_csv_count,
        "residual_plot_count": residual_plot_count,
        "jobs_with_fit_artifact_warnings": jobs_with_warnings,
    }


def origin_session_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    retries_used = 0
    stale_killed = 0
    failed_sessions = 0
    ok_after_retry = 0
    total_session_errors = 0
    for job in results:
        session = job.get("origin_session") or {}
        if session.get("retry_used"):
            retries_used += 1
        if session.get("stale_origin_killed"):
            stale_killed += 1
        if session.get("final_session_status") == "ok_after_retry":
            ok_after_retry += 1
        if session.get("final_session_status") == "failed":
            failed_sessions += 1
        total_session_errors += len(session.get("session_errors") or [])
    return {
        "jobs_with_retry_used": retries_used,
        "jobs_with_stale_origin_killed": stale_killed,
        "jobs_ok_after_retry": ok_after_retry,
        "jobs_session_failed": failed_sessions,
        "total_session_errors": total_session_errors,
    }


def session_test_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    jobs_with_retry_used = 0
    jobs_with_injection_triggered = 0
    jobs_with_cli_session_overrides = 0
    status_counts: dict[str, int] = {}
    for job in results:
        session = job.get("origin_session") or {}
        if session.get("retry_used"):
            jobs_with_retry_used += 1
        if session.get("injection_triggered"):
            jobs_with_injection_triggered += 1
        cli_overrides = session.get("cli_session_overrides") or {}
        if cli_overrides:
            jobs_with_cli_session_overrides += 1
        fss = str(session.get("final_session_status") or "unknown")
        status_counts[fss] = status_counts.get(fss, 0) + 1
    return {
        "jobs_with_retry_used": jobs_with_retry_used,
        "jobs_with_injection_triggered": jobs_with_injection_triggered,
        "jobs_with_cli_session_overrides": jobs_with_cli_session_overrides,
        "final_session_status_counts": status_counts,
    }


def session_history_summary(
    recent_window: int = 20,
    degraded_ok_after_retry_threshold: int = 3,
    degraded_failed_threshold: int = 1,
) -> dict[str, Any]:
    """Read reports/session_history.json and summarize recent health."""
    history_path = PROJECT_ROOT / "reports" / "session_history.json"
    summary: dict[str, Any] = {
        "history_path": rel(history_path),
        "entries_seen": 0,
        "recent_window": int(recent_window),
        "degraded_ok_after_retry_threshold": int(degraded_ok_after_retry_threshold),
        "degraded_failed_threshold": int(degraded_failed_threshold),
        "recent_ok": 0,
        "recent_ok_after_retry": 0,
        "recent_failed": 0,
        "recent_injection_triggered": 0,
        "health_status": "unknown",
    }
    if not history_path.exists():
        return summary
    try:
        raw = history_path.read_text(encoding="utf-8")
        entries = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return summary
    if not isinstance(entries, list):
        return summary

    summary["entries_seen"] = len(entries)
    recent = entries[-int(recent_window):] if recent_window > 0 else []
    for entry in recent:
        if not isinstance(entry, dict):
            continue
        fss = str(entry.get("final_session_status") or "")
        if fss == "ok":
            summary["recent_ok"] += 1
        elif fss == "ok_after_retry":
            summary["recent_ok_after_retry"] += 1
        elif fss == "failed":
            summary["recent_failed"] += 1
        if entry.get("injection_triggered"):
            summary["recent_injection_triggered"] += 1

    if summary["recent_failed"] >= int(degraded_failed_threshold):
        summary["health_status"] = "degraded"
    elif summary["recent_ok_after_retry"] >= int(degraded_ok_after_retry_threshold):
        summary["health_status"] = "degraded"
    else:
        summary["health_status"] = "ok"
    return summary


def derive_health_policy(results: list[dict[str, Any]]) -> dict[str, int]:
    """Pick the first job's health policy, falling back to defaults."""
    defaults = {
        "recent_window": 20,
        "degraded_ok_after_retry_threshold": 3,
        "degraded_failed_threshold": 1,
    }
    for job in results:
        session = job.get("origin_session") or {}
        effective = session.get("effective_settings") or {}
        health = effective.get("health")
        if isinstance(health, dict):
            policy = dict(defaults)
            for key in policy:
                if key in health:
                    try:
                        policy[key] = int(health[key])
                    except (TypeError, ValueError):
                        pass
            return policy
    return defaults


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

    passed_count = sum(1 for job in results if is_job_pass(job))
    failed_count = sum(1 for job in results if not is_job_pass(job))
    status = batch_status(passed_count, failed_count)
    health_policy = derive_health_policy(results)
    retry_config = create_retry_config(batch_name, results)
    report = {
        "status": status,
        "timestamp_utc": current_timestamp_utc(),
        "batch_name": batch_name,
        "job_count": len(results),
        "passed_count": passed_count,
        "failed_count": failed_count,
        "continue_on_error": continue_on_error,
        "jobs": results,
        "retry_config": retry_config,
        "style_summary": style_summary(results),
        "errorbar_summary": errorbar_summary(results),
        "fitting_summary": fitting_summary(results),
        "fit_artifact_summary": fit_artifact_summary(results),
        "origin_session_summary": origin_session_summary(results),
        "session_test_summary": session_test_summary(results),
        "session_history_summary": session_history_summary(
            recent_window=health_policy["recent_window"],
            degraded_ok_after_retry_threshold=health_policy["degraded_ok_after_retry_threshold"],
            degraded_failed_threshold=health_policy["degraded_failed_threshold"],
        ),
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
