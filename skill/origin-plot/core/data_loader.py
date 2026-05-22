"""Canonical data loader for v1.0.

Reads CSV / XLSX / TSV / TXT input files into a pandas DataFrame using the
same detection rules the legacy executor uses. Markdown / image / OCR inputs
are intentionally out of scope -- those are Codex's responsibility (see
``contracts/codex_data_wrangler_contract.md``).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import _legacy  # noqa: F401 - extends sys.path
from .paths import resolve_project_path

import origin_plot_from_config as _legacy_executor  # type: ignore[import-not-found]


SUPPORTED_FORMATS = {"auto", "csv", "xlsx", "xls", "tsv", "txt"}


def detect_format(input_path: Path, declared: str | None) -> str:
    return _legacy_executor.detect_format(input_path, declared)


def load(input_file: str, input_format: str | None = "auto", sheet_name: Any | None = None):
    """Load a canonical data file into a pandas DataFrame.

    Parameters
    ----------
    input_file:
        Project-relative path.
    input_format:
        ``auto`` (default) detects from suffix; otherwise must be one of
        :data:`SUPPORTED_FORMATS`.
    sheet_name:
        Optional Excel sheet name; ignored for non-Excel inputs.
    """
    path = resolve_project_path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"input_file does not exist: {input_file}")
    detected = detect_format(path, input_format)
    return _legacy_executor.read_dataframe(path, detected, sheet_name), detected


__all__ = ["SUPPORTED_FORMATS", "detect_format", "load"]
