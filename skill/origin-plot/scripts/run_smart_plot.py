"""Smart plotting entry point for origin-plot v0.9.

Pipeline:
1. Load the smart input config.
2. Run :mod:`analyze_data_source` to detect roles and emit a generated plot
   config plus an analysis report.
3. If the analysis is PASS / PARTIAL PASS, invoke
   ``origin_plot_from_config.py`` against the generated config.
4. Copy the produced figures, OPJU, and config into a ``report_package``
   directory so the run is portable.
5. Write a combined run report to ``reports/smart_plot_run_report.json``.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMART_RUN_REPORT_PATH = PROJECT_ROOT / "reports" / "smart_plot_run_report.json"
SINGLE_PLOT_REPORT_PATH = PROJECT_ROOT / "reports" / "origin_plot_v0_2_report.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_data_source import (  # noqa: E402
    analyze,
    load_yaml,
    rel,
    resolve_project_path,
)


def current_timestamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_origin_plot(generated_config_path: Path) -> tuple[int, str, str]:
    cmd = [
        sys.executable,
        "scripts/origin_plot_from_config.py",
        "--config",
        rel(generated_config_path).replace("\\", "/"),
    ]
    completed = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def read_report(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def output_status(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"path": None, "exists": False, "size_bytes": 0}
    exists = path.exists()
    return {
        "path": rel(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
    }


def collect_figure_outputs(plot_report: dict[str, Any]) -> dict[str, Path | None]:
    outputs = plot_report.get("outputs") or {}
    figure_outputs: dict[str, Path | None] = {"png": None, "pdf": None, "opju": None}
    for key in ("png", "pdf", "opju"):
        info = outputs.get(key) or {}
        path_value = info.get("path")
        if path_value:
            figure_outputs[key] = resolve_project_path(str(path_value))
    return figure_outputs


def build_report_package(
    package_dir: Path,
    smart_cfg_path: Path,
    analysis_report: dict[str, Any],
    plot_report: dict[str, Any] | None,
    generated_config_path: Path,
    figure_outputs: dict[str, Path | None],
    smart_run_report: dict[str, Any],
) -> dict[str, Any]:
    package_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = package_dir / "figures"
    origin_dir = package_dir / "origin_projects"
    configs_dir = package_dir / "configs"
    for sub in (figures_dir, origin_dir, configs_dir):
        sub.mkdir(parents=True, exist_ok=True)

    copied: dict[str, str] = {}
    for key, src in figure_outputs.items():
        if src is None or not src.exists():
            continue
        if key == "opju":
            dest = origin_dir / src.name
        else:
            dest = figures_dir / src.name
        try:
            shutil.copyfile(src, dest)
        except Exception as exc:  # noqa: BLE001
            smart_run_report.setdefault("warnings", []).append(
                f"failed to copy {src.name} into report package: {type(exc).__name__}: {exc}"
            )
            continue
        copied[key] = rel(dest)

    config_copy_dest = configs_dir / generated_config_path.name
    try:
        shutil.copyfile(generated_config_path, config_copy_dest)
    except Exception as exc:  # noqa: BLE001
        smart_run_report.setdefault("warnings", []).append(
            f"failed to copy generated config into report package: {type(exc).__name__}: {exc}"
        )

    figure_index_lines = [
        "# Smart Plot Run Index",
        "",
        f"- timestamp_utc: {smart_run_report['timestamp_utc']}",
        f"- input_file: {analysis_report.get('input_file')}",
        f"- detected_format: {analysis_report.get('detected_format')}",
        f"- recommended_graph_type: {analysis_report.get('recommended_graph_type')}",
        f"- selected_roles: {json.dumps(analysis_report.get('selected_roles'), ensure_ascii=False)}",
        "",
        "## Outputs",
        "",
    ]
    for key in ("png", "pdf", "opju"):
        if key in copied:
            figure_index_lines.append(f"- {key.upper()}: `{copied[key]}`")
    figure_index_lines.append("")
    figure_index_lines.append("## Generated config")
    figure_index_lines.append("")
    figure_index_lines.append(f"- `{rel(config_copy_dest)}`")
    figure_index_lines.append("")
    figure_index_lines.append("## Smart input config")
    figure_index_lines.append("")
    figure_index_lines.append(f"- `{rel(smart_cfg_path)}`")

    (package_dir / "figure_index.md").write_text(
        "\n".join(figure_index_lines), encoding="utf-8"
    )
    (package_dir / "run_report.json").write_text(
        json.dumps(smart_run_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return {
        "package_dir": rel(package_dir),
        "figures": copied,
        "config_copy": rel(config_copy_dest),
        "figure_index": rel(package_dir / "figure_index.md"),
        "run_report_copy": rel(package_dir / "run_report.json"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run end-to-end smart plotting pipeline.")
    parser.add_argument(
        "--config",
        default="configs/smart/smart_input_config.yaml",
        help="Smart input config YAML (relative to project root).",
    )
    parser.add_argument(
        "--input-file",
        default=None,
        help="Override input_file from the smart config (relative path).",
    )
    args = parser.parse_args()

    timestamp = current_timestamp_utc()
    smart_run_report: dict[str, Any] = {
        "timestamp_utc": timestamp,
        "status": "FAIL",
        "analysis_report": None,
        "generated_config": None,
        "origin_plot_report": None,
        "report_package": None,
        "final_outputs": {
            "png": output_status(None),
            "pdf": output_status(None),
            "opju": output_status(None),
        },
        "warnings": [],
        "errors": [],
    }

    config_path = resolve_project_path(args.config)
    if not config_path.exists():
        smart_run_report["errors"].append(f"smart config does not exist: {rel(config_path)}")
        SMART_RUN_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SMART_RUN_REPORT_PATH.write_text(
            json.dumps(smart_run_report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"FAIL: {smart_run_report['errors'][0]}")
        return 1

    smart_cfg = load_yaml(config_path)
    if args.input_file:
        smart_cfg["input_file"] = args.input_file

    try:
        analysis_report = analyze(smart_cfg)
    except Exception as exc:  # noqa: BLE001
        smart_run_report["errors"].append(
            f"smart analysis failed: {type(exc).__name__}: {exc}"
        )
        SMART_RUN_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SMART_RUN_REPORT_PATH.write_text(
            json.dumps(smart_run_report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"FAIL: {smart_run_report['errors'][-1]}")
        return 1

    smart_run_report["analysis_report"] = analysis_report.get("status")
    smart_run_report["warnings"].extend(analysis_report.get("warnings") or [])
    output_cfg = smart_cfg.get("output") or {}
    generated_config_value = output_cfg.get(
        "generated_config_path", "configs/generated/smart_generated_plot_config.yaml"
    )
    generated_config_path = resolve_project_path(str(generated_config_value))
    smart_run_report["generated_config"] = rel(generated_config_path)

    if analysis_report.get("status") == "FAIL":
        smart_run_report["errors"].append("smart analysis returned FAIL; not invoking Origin")
        SMART_RUN_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SMART_RUN_REPORT_PATH.write_text(
            json.dumps(smart_run_report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("FAIL: smart analysis returned FAIL")
        return 1

    rc, stdout, stderr = run_origin_plot(generated_config_path)
    if stdout:
        print(stdout, end="")
    if stderr and rc != 0:
        print(stderr, end="")

    plot_report = read_report(SINGLE_PLOT_REPORT_PATH)
    if plot_report is None:
        smart_run_report["errors"].append("origin_plot did not produce a report")
        SMART_RUN_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SMART_RUN_REPORT_PATH.write_text(
            json.dumps(smart_run_report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("FAIL: origin_plot did not produce a report")
        return 1

    smart_run_report["origin_plot_report"] = plot_report.get("status")

    figure_outputs = collect_figure_outputs(plot_report)
    smart_run_report["final_outputs"] = {
        key: output_status(path) for key, path in figure_outputs.items()
    }

    report_package_value = output_cfg.get("report_package_dir") or "reports/report_package"
    package_dir = resolve_project_path(str(report_package_value))
    smart_run_report["report_package"] = build_report_package(
        package_dir,
        config_path,
        analysis_report,
        plot_report,
        generated_config_path,
        figure_outputs,
        smart_run_report,
    )

    pass_statuses = {"PASS", "PASS with warnings", "PASS with session_retry"}
    plot_status = str(plot_report.get("status") or "")
    has_all_outputs = all(
        info.get("exists") for info in smart_run_report["final_outputs"].values()
    )

    if plot_status in pass_statuses and has_all_outputs:
        if analysis_report.get("status") == "PARTIAL PASS":
            smart_run_report["status"] = "PARTIAL PASS"
        else:
            smart_run_report["status"] = "PASS"
    elif has_all_outputs:
        smart_run_report["status"] = "PARTIAL PASS"
        smart_run_report["warnings"].append(
            f"plot status was {plot_status!r}; outputs exist so reporting PARTIAL PASS"
        )
    else:
        smart_run_report["status"] = "FAIL"
        smart_run_report["errors"].append(
            f"plot status={plot_status!r}, outputs incomplete"
        )

    SMART_RUN_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SMART_RUN_REPORT_PATH.write_text(
        json.dumps(smart_run_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"smart_plot_status: {smart_run_report['status']}")
    print(f"report: {rel(SMART_RUN_REPORT_PATH)}")
    if smart_run_report["status"] in {"PASS", "PARTIAL PASS"}:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
