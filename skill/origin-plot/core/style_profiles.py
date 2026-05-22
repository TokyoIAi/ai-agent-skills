"""Helpers for loading reusable style + export profiles.

These are thin wrappers around the legacy helpers so the v1.0 core layer can
load a style or export YAML without re-implementing format detection or merge
priority.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import _legacy  # noqa: F401 - extends sys.path

import origin_plot_from_config as _legacy_executor  # type: ignore[import-not-found]


def load_style_profile(config: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    return _legacy_executor.load_optional_profile(config, "style_profile")


def load_export_profile(config: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    return _legacy_executor.load_optional_profile(config, "export_profile")


def effective_export_settings(
    config: dict[str, Any],
    style_profile: dict[str, Any],
    export_profile: dict[str, Any],
) -> dict[str, Any]:
    return _legacy_executor.effective_export_settings(config, style_profile, export_profile)


__all__ = [
    "load_style_profile",
    "load_export_profile",
    "effective_export_settings",
]
