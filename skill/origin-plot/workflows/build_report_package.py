"""Rebuild ``reports/report_package/`` from an existing legacy report.

Useful when a single-plot run completed but the report_package needs to be
regenerated (e.g. after manual cleanup). Reads
``reports/origin_plot_v0_2_report.json`` and copies the recorded outputs plus
the originating plot config into the package directory.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.paths import current_timestamp_utc, rel, resolve_project_path  # noqa: E402
from core.report_writer import (  # noqa: E402
    REPORT_PACKAGE_DIR,
    assemble_report_package,
    collect_outputs,
    output_status,
)


def load_legacy_report(report_path: Path) -> dict[str, Any]:
    if not report_path.exists():
        raise FileNotFoundError(f"legacy report does not exist: {rel(report_path)}")
    return json.loads(report_path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild reports/report_package/ from a legacy report.")
    parser.add_argument(
        "--report",
        default="reports/origin_plot_v0_2_report.json",
        help="Legacy single-plot report JSON to source paths from.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Plot config to include in the package (defaults to report.config_path).",
    )
    args = parser.parse_args()

    legacy_path = resolve_project_path(args.report)
    legacy_report = load_legacy_report(legacy_path)

    config_value = args.config or legacy_report.get("config_path")
    if not config_value:
        print("FAIL: cannot resolve plot config path; pass --config explicitly.")
        return 1
    config_path = resolve_project_path(str(config_value))

    outputs = collect_outputs(legacy_report)
    summary: dict[str, Any] = {
        "timestamp_utc": current_timestamp_utc(),
        "status": legacy_report.get("status") or "UNKNOWN",
        "config_path": rel(config_path),
        "input_file": legacy_report.get("input_file"),
        "graph_type": legacy_report.get("graph_type"),
        "outputs": {key: output_status(path) for key, path in outputs.items()},
        "warnings": [],
        "source_legacy_report": rel(legacy_path),
    }
    summary["report_package"] = assemble_report_package(
        REPORT_PACKAGE_DIR,
        [config_path],
        outputs,
        summary,
    )
    print(f"report_package: {summary['report_package']['package_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
