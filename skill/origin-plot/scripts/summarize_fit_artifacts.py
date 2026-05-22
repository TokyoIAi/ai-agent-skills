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
        summary["reports_scanned"] += 1
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


def discover_reports_from_dir(reports_dir: Path) -> list[Path]:
    if not reports_dir.exists() or not reports_dir.is_dir():
        return []
    return sorted(p for p in reports_dir.glob("*.json") if p.is_file())


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
    args = parser.parse_args()

    paths: list[Path] = []
    for value in args.reports:
        paths.append(resolve_project_path(value))
    if args.reports_dir:
        for entry in discover_reports_from_dir(resolve_project_path(args.reports_dir)):
            if entry not in paths:
                paths.append(entry)

    if Path(args.output).is_absolute():
        print(f"FAIL: --output must be a relative path: {args.output}")
        return 1

    output_path = resolve_project_path(args.output)
    # Avoid scanning the artifact report we are about to write.
    paths = [p for p in paths if p.resolve() != output_path.resolve()]

    reports_data: list[tuple[Path, dict[str, Any] | None]] = []
    for path in paths:
        if not path.exists():
            reports_data.append((path, None))
        else:
            reports_data.append((path, read_report(path)))

    summary = collect_artifacts(reports_data)
    summary["scanned_paths"] = [rel(path) for path, _ in reports_data]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

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
