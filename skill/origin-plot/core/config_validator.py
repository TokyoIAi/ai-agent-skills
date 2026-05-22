"""Validation entry point for plot configs.

Wraps the v0.8.7 validator (``scripts/validate_origin_plot_config.py``). The
``core`` layer keeps this thin so the verified validation logic stays the
single source of truth.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import _legacy  # noqa: F401 - side-effect: extends sys.path
from .paths import PROJECT_ROOT, rel, resolve_project_path

import validate_origin_plot_config as _legacy_validator  # type: ignore[import-not-found]


def validate(config_path: Path | str) -> dict[str, Any]:
    """Validate a plot config and return the structured summary.

    The legacy validator prints to stdout and may raise ``SystemExit(1)`` on
    fatal errors. Callers that need a non-fatal mode should catch
    ``SystemExit`` themselves.
    """
    path = resolve_project_path(str(config_path)) if not Path(config_path).is_absolute() else Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"plot config does not exist: {rel(path)}")
    config = _legacy_validator.load_yaml(path)
    summary, _df = _legacy_validator.validate_config(config)
    summary["config_path"] = rel(path)
    return summary


__all__ = ["validate"]
