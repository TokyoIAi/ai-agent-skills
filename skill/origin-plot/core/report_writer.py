"""Report and report_package writers for v1.0 workflows."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT, current_timestamp_utc, rel, resolve_project_path

REPORT_PACKAGE_DIR = PROJECT_ROOT / "reports" / "report_package"


def write_run_report(
    target_path: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def output_status(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"path": None, "exists": False, "size_bytes": 0}
    exists = path.exists()
    return {
        "path": rel(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
    }


def collect_outputs(legacy_report: dict[str, Any] | None) -> dict[str, Path | None]:
    """Pull PNG / PDF / OPJU output paths from a legacy single-plot report."""
    outputs: dict[str, Path | None] = {"png": None, "pdf": None, "opju": None}
    if not legacy_report:
        return outputs
    for key in outputs:
        info = (legacy_report.get("outputs") or {}).get(key) or {}
        path_value = info.get("path")
        if path_value:
            outputs[key] = resolve_project_path(str(path_value))
    return outputs


def assemble_report_package(
    package_dir: Path,
    config_paths: list[Path],
    output_paths: dict[str, Path | None],
    summary: dict[str, Any],
) -> dict[str, Any]:
    """Copy current-run artifacts into the project's report_package directory."""
    figures_dir = package_dir / "figures"
    origin_dir = package_dir / "origin_projects"
    configs_dir = package_dir / "configs"
    for sub in (figures_dir, origin_dir, configs_dir):
        sub.mkdir(parents=True, exist_ok=True)

    copied: dict[str, str] = {}
    for key, src in output_paths.items():
        if src is None or not src.exists():
            continue
        dest_dir = origin_dir if key == "opju" else figures_dir
        dest = dest_dir / src.name
        try:
            shutil.copyfile(src, dest)
            copied[key] = rel(dest)
        except Exception as exc:  # noqa: BLE001 - copy is best-effort
            summary.setdefault("warnings", []).append(
                f"failed to copy {src.name} into report package: {type(exc).__name__}: {exc}"
            )

    config_copies: list[str] = []
    for cfg in config_paths:
        if not cfg.exists():
            continue
        dest = configs_dir / cfg.name
        try:
            shutil.copyfile(cfg, dest)
            config_copies.append(rel(dest))
        except Exception as exc:  # noqa: BLE001
            summary.setdefault("warnings", []).append(
                f"failed to copy config {cfg.name} into report package: {type(exc).__name__}: {exc}"
            )

    figure_index = package_dir / "figure_index.md"
    config_lines = "\n".join(f"- `{p}`" for p in config_copies) or "_(none)_"
    figure_index.write_text(
        "\n".join(
            [
                "# origin-plot run index",
                "",
                f"- timestamp_utc: {summary.get('timestamp_utc', current_timestamp_utc())}",
                f"- status: {summary.get('status')}",
                f"- input_file: {summary.get('input_file')}",
                f"- graph_type: {summary.get('graph_type')}",
                "",
                "## Figures",
                "",
                *(f"- {key.upper()}: `{copied[key]}`" for key in ("png", "pdf", "opju") if key in copied),
                "",
                "## Configs",
                "",
                config_lines,
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    run_report = package_dir / "run_report.json"
    run_report.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return {
        "package_dir": rel(package_dir),
        "figures": copied,
        "config_copies": config_copies,
        "figure_index": rel(figure_index),
        "run_report": rel(run_report),
    }


__all__ = [
    "REPORT_PACKAGE_DIR",
    "assemble_report_package",
    "collect_outputs",
    "output_status",
    "write_run_report",
]
