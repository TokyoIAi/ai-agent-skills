"""origin-plot v1.0 single-plot entry point.

Validates the config, runs the verified Origin executor, copies the produced
PNG / PDF / OPJU into ``reports/report_package/``, and writes a minimal run
report. The legacy ``scripts/origin_plot_from_config.py`` remains the source
of truth for Origin control.

Usage (from ``skill/origin-plot/``)::

    py workflows\\run_plot.py --config configs\\examples\\line_plot.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Allow ``core`` imports when running as a script.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.config_validator import validate  # noqa: E402
from core.origin_executor import execute  # noqa: E402
from core.paths import current_timestamp_utc, rel, resolve_project_path  # noqa: E402
from core.report_writer import (  # noqa: E402
    REPORT_PACKAGE_DIR,
    assemble_report_package,
    collect_outputs,
    output_status,
    write_run_report,
)


PASS_STATUSES = {"PASS", "PASS with warnings", "PASS with session_retry"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a single plot via the v1.0 core layer.")
    parser.add_argument("--config", required=True, help="Plot config YAML (relative path).")
    parser.add_argument(
        "--no-package",
        action="store_true",
        help="Skip building reports/report_package/ for this run.",
    )
    args = parser.parse_args()

    config_path = resolve_project_path(args.config)
    if not config_path.exists():
        print(f"FAIL: plot config not found: {rel(config_path)}")
        return 1

    summary: dict[str, Any] = {
        "timestamp_utc": current_timestamp_utc(),
        "status": "FAIL",
        "config_path": rel(config_path),
        "input_file": None,
        "graph_type": None,
        "validation": None,
        "execution": None,
        "outputs": {key: output_status(None) for key in ("png", "pdf", "opju")},
        "report_package": None,
        "warnings": [],
        "errors": [],
    }

    try:
        validation_summary = validate(config_path)
    except SystemExit as exc:
        summary["errors"].append(f"validation exited: {exc.code}")
        write_run_report(REPORT_PACKAGE_DIR / "run_report.json", summary)
        print(f"FAIL: validation failed for {rel(config_path)}")
        return 1
    except Exception as exc:  # noqa: BLE001 - surface the failure clearly
        summary["errors"].append(f"validation error: {type(exc).__name__}: {exc}")
        write_run_report(REPORT_PACKAGE_DIR / "run_report.json", summary)
        print(f"FAIL: validation error: {exc}")
        return 1

    summary["validation"] = "PASS"
    summary["input_file"] = validation_summary.get("input_file")
    summary["graph_type"] = validation_summary.get("graph_type")

    result = execute(rel(config_path).replace("\\", "/"))
    summary["execution"] = {
        "returncode": result["returncode"],
        "report_path": result["report_path"],
        "report_status": (result["report"] or {}).get("status"),
    }
    if result["stdout"]:
        sys.stdout.write(result["stdout"])
    if result["stderr"] and result["returncode"] != 0:
        sys.stderr.write(result["stderr"])

    legacy_report = result["report"] or {}
    output_paths = collect_outputs(legacy_report)
    summary["outputs"] = {key: output_status(path) for key, path in output_paths.items()}

    requested_outputs = legacy_report.get("outputs") or {}
    requested_keys = [key for key, info in requested_outputs.items() if info and info.get("path")]
    missing = [
        key for key in requested_keys
        if not summary["outputs"].get(key, {}).get("exists")
    ]
    legacy_status = (legacy_report.get("status") or "").strip()

    if result["returncode"] == 0 and legacy_status in PASS_STATUSES and not missing:
        summary["status"] = legacy_status if legacy_status != "PASS" else "PASS"
    elif result["returncode"] == 0 and not missing:
        summary["status"] = "PASS with warnings"
        summary["warnings"].append(
            f"legacy reported status={legacy_status!r}; outputs exist so reporting PASS with warnings"
        )
    else:
        summary["status"] = "FAIL"
        if missing:
            summary["errors"].append(f"missing outputs: {missing}")

    if not args.no_package:
        summary["report_package"] = assemble_report_package(
            REPORT_PACKAGE_DIR,
            [config_path],
            output_paths,
            summary,
        )
        # Re-write run_report.json so it reflects the final summary including
        # the report_package block.
        write_run_report(REPORT_PACKAGE_DIR / "run_report.json", summary)
    else:
        write_run_report(REPORT_PACKAGE_DIR / "run_report.json", summary)

    print(f"run_plot status: {summary['status']}")
    print(f"report_package: {(summary['report_package'] or {}).get('package_dir')}")
    return 0 if summary["status"] in PASS_STATUSES else 1


if __name__ == "__main__":
    raise SystemExit(main())
