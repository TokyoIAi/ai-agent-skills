"""Summarize fit artifacts across one or more origin-plot reports.

Reads the structured single-plot or batch report JSON files and writes
``reports/origin_plot_v0_8_artifact_report.json`` with cross-report counts and
artifact existence checks. Only relative paths are emitted.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "reports" / "origin_plot_v0_8_artifact_report.json"


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


def read_report(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - report failures should be reflected, not raised
        return None


def iter_single_reports(report: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """Yield single-plot style report dicts from either single or batch reports."""
    if "fitting_annotation" in report or "fitting_summary_csv" in report or "residuals" in report:
        yield report
    for job in report.get("jobs") or []:
        if isinstance(job, dict):
            yield job


def check_artifact(path_value: Any) -> tuple[str | None, bool]:
    if not path_value or not isinstance(path_value, str):
        return None, False
    candidate = resolve_project_path(path_value)
    return rel(candidate), candidate.exists()


def collect_artifacts(reports_data: list[tuple[Path, dict[str, Any] | None]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "status": "PASS",
        "reports_scanned": 0,
        "reports_unreadable": [],
        "fit_models_seen": 0,
        "annotations_requested": 0,
        "annotations_applied": 0,
        "summary_csv_outputs": [],
        "residual_csv_outputs": [],
        "residual_plot_outputs": [],
        "health_status_counts": {"ok": 0, "degraded": 0, "unknown": 0},
        "reports_with_health_status": 0,
        "reports_without_health_status": 0,
        "warnings": [],
        "missing_artifacts": [],
    }

    seen_summary_csv: set[str] = set()
    seen_residual_csv: set[str] = set()
    seen_residual_plot: set[str] = set()

    for report_path, report in reports_data:
        if report is None:
            summary["reports_unreadable"].append(rel(report_path))
            continue
        if not isinstance(report, dict):
            summary["reports_unreadable"].append(rel(report_path))
            continue
        summary["reports_scanned"] += 1

        # Health status rollup: prefer batch-level session_history_summary,
        # fall back to single-plot session_health_snapshot.
        health_status: str | None = None
        history_summary = report.get("session_history_summary")
        if isinstance(history_summary, dict) and history_summary.get("health_status"):
            health_status = str(history_summary.get("health_status"))
        else:
            snapshot = report.get("session_health_snapshot")
            if isinstance(snapshot, dict) and snapshot.get("health_status"):
                health_status = str(snapshot.get("health_status"))
        if health_status is not None:
            summary["reports_with_health_status"] += 1
            counts = summary["health_status_counts"]
            counts[health_status] = int(counts.get(health_status, 0)) + 1
        else:
            summary["reports_without_health_status"] += 1

        for entry in iter_single_reports(report):
            fitting = entry.get("fitting") or {}
            fit_models = fitting.get("models") or []
            summary["fit_models_seen"] += len(fit_models)

            annotation = entry.get("fitting_annotation") or {}
            if annotation.get("requested"):
                summary["annotations_requested"] += 1
            if annotation.get("applied"):
                summary["annotations_applied"] += 1
            for warning in annotation.get("warnings") or []:
                summary["warnings"].append(f"annotation: {warning}")

            summary_csv = entry.get("fitting_summary_csv") or {}
            if summary_csv.get("requested"):
                csv_rel, csv_exists = check_artifact(summary_csv.get("path"))
                if csv_rel and csv_rel not in seen_summary_csv:
                    seen_summary_csv.add(csv_rel)
                    summary["summary_csv_outputs"].append(
                        {
                            "path": csv_rel,
                            "exists": csv_exists,
                            "rows_written": int(summary_csv.get("rows_written") or 0),
                            "append": bool(summary_csv.get("append", True)),
                        }
                    )
                    if not csv_exists:
                        summary["missing_artifacts"].append(csv_rel)
            for warning in summary_csv.get("warnings") or []:
                summary["warnings"].append(f"summary_csv: {warning}")

            residuals = entry.get("residuals") or {}
            for record in residuals.get("csv_outputs") or []:
                csv_rel, csv_exists = check_artifact(record.get("path"))
                if csv_rel and csv_rel not in seen_residual_csv:
                    seen_residual_csv.add(csv_rel)
                    summary["residual_csv_outputs"].append(
                        {
                            "fit_name": record.get("fit_name"),
                            "path": csv_rel,
                            "exists": csv_exists,
                            "rows_written": int(record.get("rows_written") or 0),
                        }
                    )
                    if not csv_exists:
                        summary["missing_artifacts"].append(csv_rel)
            for record in residuals.get("residual_plot_outputs") or []:
                png_rel, png_exists = check_artifact(record.get("png"))
                pdf_rel, pdf_exists = check_artifact(record.get("pdf"))
                key = f"{png_rel or ''}|{pdf_rel or ''}"
                if key in seen_residual_plot:
                    continue
                seen_residual_plot.add(key)
                summary["residual_plot_outputs"].append(
                    {
                        "fit_name": record.get("fit_name"),
                        "png": png_rel,
                        "png_exists": png_exists,
                        "pdf": pdf_rel,
                        "pdf_exists": pdf_exists,
                    }
                )
                if png_rel and not png_exists:
                    summary["missing_artifacts"].append(png_rel)
                if pdf_rel and not pdf_exists:
                    summary["missing_artifacts"].append(pdf_rel)
            for warning in residuals.get("warnings") or []:
                summary["warnings"].append(f"residuals: {warning}")

    if summary["reports_unreadable"]:
        summary["warnings"].append(
            f"{len(summary['reports_unreadable'])} report(s) could not be read"
        )

    if summary["missing_artifacts"]:
        summary["status"] = "PASS with warnings"
    if summary["reports_scanned"] == 0:
        summary["status"] = "FAIL"
    return summary


def discover_reports_from_dir(reports_dir: Path, output_path: Path) -> list[Path]:
    if not reports_dir.exists() or not reports_dir.is_dir():
        return []
    output_resolved = output_path.resolve()
    skip_names = {"origin_plot_v0_8_artifact_report.json", "session_history.json", "session_history.bak.json"}
    discovered: list[Path] = []
    for entry in sorted(reports_dir.glob("*.json")):
        if not entry.is_file():
            continue
        # Skip the artifact summary itself and non-report JSON files.
        if entry.resolve() == output_resolved:
            continue
        if entry.name in skip_names:
            continue
        # Skip .bak.json siblings used by the reset workflow.
        if entry.name.endswith(".bak.json"):
            continue
        discovered.append(entry)
    return discovered


def is_injection_report(report: dict[str, Any]) -> bool:
    """Return True if the report was produced with session error injection enabled."""
    # Single-plot report: check top-level origin_session.
    session = report.get("origin_session") or {}
    if session.get("injection_triggered"):
        return True
    effective = session.get("effective_settings") or {}
    if effective.get("inject_session_error_once"):
        return True
    # Batch report: check if any job used injection.
    for job in report.get("jobs") or []:
        if not isinstance(job, dict):
            continue
        job_session = job.get("origin_session") or {}
        if job_session.get("injection_triggered"):
            return True
        job_effective = job_session.get("effective_settings") or {}
        if job_effective.get("inject_session_error_once"):
            return True
    return False


def filter_reports_by_injection(
    reports_data: list[tuple[Path, dict[str, Any] | None]],
    injection_filter: str,
) -> list[tuple[Path, dict[str, Any] | None]]:
    """Apply injection filter to loaded reports."""
    if injection_filter == "include_all":
        return reports_data
    filtered: list[tuple[Path, dict[str, Any] | None]] = []
    for path, report in reports_data:
        if report is None:
            filtered.append((path, report))
            continue
        if not isinstance(report, dict):
            filtered.append((path, report))
            continue
        is_inj = is_injection_report(report)
        if injection_filter == "exclude_injection" and is_inj:
            continue
        if injection_filter == "include_injection_only" and not is_inj:
            continue
        filtered.append((path, report))
    return filtered


def parse_since(value: str | None) -> str | None:
    """Normalize --since to an ISO timestamp string suitable for lex compare."""
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    # Accept YYYY-MM-DD or full ISO; pad date-only with T00:00:00Z for consistency.
    if len(cleaned) == 10 and cleaned[4] == "-" and cleaned[7] == "-":
        cleaned = cleaned + "T00:00:00Z"
    elif "T" in cleaned and not cleaned.endswith("Z"):
        cleaned = cleaned + "Z"
    return cleaned


def report_timestamp(report: dict[str, Any]) -> str | None:
    """Best-effort retrieval of a report's timestamp."""
    ts = report.get("timestamp_utc")
    if isinstance(ts, str) and ts:
        return ts
    return None


def filter_reports_by_since(
    reports_data: list[tuple[Path, dict[str, Any] | None]],
    since: str | None,
    drop_missing_timestamp: bool = False,
) -> tuple[list[tuple[Path, dict[str, Any] | None]], int, int, list[str]]:
    """Filter reports by ``--since`` and optionally drop reports without a timestamp.

    Returns (kept_reports, skipped_by_since, skipped_missing_timestamp, warnings).
    """
    if not since:
        return reports_data, 0, 0, []
    kept: list[tuple[Path, dict[str, Any] | None]] = []
    skipped_since = 0
    skipped_missing = 0
    warnings: list[str] = []
    for path, report in reports_data:
        if report is None or not isinstance(report, dict):
            kept.append((path, report))
            continue
        ts = report_timestamp(report)
        if ts is None:
            if drop_missing_timestamp:
                skipped_missing += 1
                continue
            warnings.append(
                f"report has no timestamp; kept regardless of --since: {rel(path)}"
            )
            kept.append((path, report))
            continue
        if ts < since:
            skipped_since += 1
            continue
        kept.append((path, report))
    return kept, skipped_since, skipped_missing, warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize fit artifacts across origin-plot reports."
    )
    parser.add_argument(
        "--reports",
        nargs="*",
        default=[],
        help="One or more report JSON paths (relative to project root).",
    )
    parser.add_argument(
        "--reports-dir",
        default=None,
        help="Optional directory whose top-level *.json files will be scanned.",
    )
    parser.add_argument(
        "--output",
        default="reports/origin_plot_v0_8_artifact_report.json",
        help="Destination report JSON (relative path).",
    )
    parser.add_argument(
        "--exclude-injection",
        action="store_true",
        help="Exclude reports produced with inject_session_error_once=true.",
    )
    parser.add_argument(
        "--include-injection",
        action="store_true",
        help="Explicitly include injection reports (default behavior, marks the filter in output).",
    )
    parser.add_argument(
        "--include-injection-only",
        action="store_true",
        help="Include only injection reports.",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="Filter reports whose timestamp is older than this (YYYY-MM-DD or full ISO Zulu).",
    )
    parser.add_argument(
        "--drop-missing-timestamp",
        action="store_true",
        help="When --since is active, also drop reports lacking timestamp_utc instead of keeping them.",
    )
    args = parser.parse_args()

    # Determine injection filter.
    if args.exclude_injection:
        injection_filter = "exclude_injection"
    elif args.include_injection_only:
        injection_filter = "include_injection_only"
    elif args.include_injection:
        injection_filter = "include_injection"
    else:
        injection_filter = "include_all"

    if Path(args.output).is_absolute():
        print(f"FAIL: --output must be a relative path: {args.output}")
        return 1
    output_path = resolve_project_path(args.output)

    paths: list[Path] = []
    for value in args.reports:
        paths.append(resolve_project_path(value))
    reports_dir_value: str | None = None
    if args.reports_dir:
        reports_dir_value = args.reports_dir
        for entry in discover_reports_from_dir(resolve_project_path(args.reports_dir), output_path):
            if entry not in paths:
                paths.append(entry)

    if reports_dir_value and not args.reports:
        input_mode = "reports_dir"
    elif reports_dir_value and args.reports:
        input_mode = "mixed"
    else:
        input_mode = "reports"

    # Avoid scanning the artifact report we are about to write even if explicitly listed.
    paths = [p for p in paths if p.resolve() != output_path.resolve()]

    reports_data: list[tuple[Path, dict[str, Any] | None]] = []
    for path in paths:
        if not path.exists():
            reports_data.append((path, None))
        else:
            reports_data.append((path, read_report(path)))

    reports_data = filter_reports_by_injection(reports_data, injection_filter)

    since_value = parse_since(args.since)
    reports_data, since_skipped, missing_ts_skipped, since_warnings = filter_reports_by_since(
        reports_data, since_value, drop_missing_timestamp=bool(args.drop_missing_timestamp)
    )

    summary = collect_artifacts(reports_data)
    summary["timestamp_utc"] = current_timestamp_utc()
    summary["input_mode"] = input_mode
    summary["reports_dir"] = reports_dir_value
    summary["injection_filter"] = injection_filter
    summary["since"] = since_value
    summary["reports_skipped_by_since"] = since_skipped
    summary["drop_missing_timestamp"] = bool(args.drop_missing_timestamp)
    summary["reports_skipped_missing_timestamp"] = missing_ts_skipped
    if since_warnings:
        summary.setdefault("warnings", []).extend(since_warnings)
    summary["scanned_paths"] = [rel(path) for path, _ in reports_data]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"input_mode: {input_mode}")
    print(f"reports_scanned: {summary['reports_scanned']}")
    print(f"fit_models_seen: {summary['fit_models_seen']}")
    print(f"annotations_requested: {summary['annotations_requested']}")
    print(f"annotations_applied: {summary['annotations_applied']}")
    print(f"summary_csv_outputs: {len(summary['summary_csv_outputs'])}")
    print(f"residual_csv_outputs: {len(summary['residual_csv_outputs'])}")
    print(f"residual_plot_outputs: {len(summary['residual_plot_outputs'])}")
    print(f"missing_artifacts: {len(summary['missing_artifacts'])}")
    print(f"status: {summary['status']}")
    print(f"output: {rel(output_path)}")

    return 0 if summary["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
