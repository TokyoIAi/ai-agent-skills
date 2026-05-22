"""Origin execution facade for v1.0 workflows.

The legacy ``origin_plot_from_config.py`` script is the verified Origin
control implementation. The v1.0 ``core`` layer never re-implements that
logic; it shells out so any future refactor can replace the backend without
touching ``workflows/``.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import _legacy  # noqa: F401 - extends sys.path
from .paths import PROJECT_ROOT, rel

LEGACY_SCRIPT = PROJECT_ROOT / "scripts" / "origin_plot_from_config.py"
LEGACY_SINGLE_REPORT = PROJECT_ROOT / "reports" / "origin_plot_v0_2_report.json"


def execute(config_path: Path | str, *, extra_args: list[str] | None = None) -> dict[str, Any]:
    """Run the legacy executor against ``config_path``.

    Returns a dict with ``returncode``, ``stdout``, ``stderr``, the rendered
    config path, and a ``report`` field that mirrors the most recent
    ``reports/origin_plot_v0_2_report.json`` produced by the legacy script.
    """
    if not LEGACY_SCRIPT.exists():
        raise RuntimeError(
            "legacy origin_plot_from_config.py is missing; refactor would break Origin control"
        )
    cmd: list[str] = [
        sys.executable,
        str(LEGACY_SCRIPT.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "--config",
        str(config_path).replace("\\", "/"),
    ]
    if extra_args:
        cmd.extend(extra_args)
    completed = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    report: dict[str, Any] | None = None
    if LEGACY_SINGLE_REPORT.exists():
        try:
            report = json.loads(LEGACY_SINGLE_REPORT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = None
    return {
        "command": cmd,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "report_path": rel(LEGACY_SINGLE_REPORT) if LEGACY_SINGLE_REPORT.exists() else None,
        "report": report,
    }


__all__ = ["execute", "LEGACY_SCRIPT", "LEGACY_SINGLE_REPORT"]
