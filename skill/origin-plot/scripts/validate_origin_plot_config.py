from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_GRAPH_TYPES = {"line", "scatter", "line_symbol", "errorbar"}
SUPPORTED_FORMATS = {"auto", "csv", "xlsx", "xls", "tsv", "txt"}
EXPORT_KEYS = ("export_png", "export_pdf", "save_opju", "png_width")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ModuleNotFoundError:
        fail("Please install PyYAML: py -m pip install pyyaml")

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        fail("Config must be a YAML mapping.")
    return data


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def load_optional_profile(config: dict[str, Any], key: str) -> tuple[str | None, dict[str, Any]]:
    value = config.get(key)
    if not value:
        return None, {}
    path = resolve_project_path(str(value))
    if not path.exists():
        fail(f"{key} does not exist: {path}")
    profile = load_yaml(path)
    return rel(path), profile


def effective_export_settings(config: dict[str, Any], style_profile: dict[str, Any], export_profile: dict[str, Any]) -> dict[str, Any]:
    settings: dict[str, Any] = {}
    style_export = style_profile.get("export") if isinstance(style_profile, dict) else None
    if isinstance(style_export, dict):
        settings.update({key: style_export[key] for key in EXPORT_KEYS if key in style_export})
    settings.update({key: export_profile[key] for key in EXPORT_KEYS if key in export_profile})
    settings.update({key: config[key] for key in EXPORT_KEYS if key in config})
    settings.setdefault("export_png", True)
    settings.setdefault("export_pdf", True)
    settings.setdefault("save_opju", True)
    settings.setdefault("png_width", 0)
    try:
        settings["png_width"] = int(settings["png_width"])
    except (TypeError, ValueError):
        fail("Effective png_width must be an integer.")
    return settings


def validate_errorbar_columns(config: dict[str, Any], df: Any, y_columns: list[str]) -> tuple[dict[str, str], str | None, list[str]]:
    warnings: list[str] = []
    y_error_columns = config.get("y_error_columns") or {}
    x_error_column = config.get("x_error_column")
    graph_type = str(config.get("graph_type", "")).lower()

    if graph_type == "errorbar" and not y_error_columns:
        warnings.append("graph_type=errorbar but y_error_columns is missing; plotting may downgrade to ordinary plot.")
        y_error_columns = {}
    if y_error_columns and not isinstance(y_error_columns, dict):
        fail("y_error_columns must be a mapping from Y column to error column.")

    normalized_y_errors: dict[str, str] = {}
    for y_col, err_col in y_error_columns.items():
        y_col = str(y_col)
        err_col = str(err_col)
        if y_col not in y_columns:
            fail(f"y_error_columns key must be one of y_columns: {y_col}")
        if err_col not in df.columns:
            fail(f"y error column does not exist: {err_col}")
        values = __import__("pandas").to_numeric(df[err_col], errors="coerce")
        if values.dropna().empty:
            fail(f"y error column is not numeric: {err_col}")
        if (values.dropna() < 0).any():
            fail(f"y error column contains negative values: {err_col}")
        normalized_y_errors[y_col] = err_col

    normalized_x_error = None
    if x_error_column not in (None, ""):
        normalized_x_error = str(x_error_column)
        if normalized_x_error not in df.columns:
            fail(f"x_error_column does not exist: {normalized_x_error}")
        values = __import__("pandas").to_numeric(df[normalized_x_error], errors="coerce")
        if values.dropna().empty:
            fail(f"x_error_column is not numeric: {normalized_x_error}")
        if (values.dropna() < 0).any():
            fail(f"x_error_column contains negative values: {normalized_x_error}")

    return normalized_y_errors, normalized_x_error, warnings


def detect_format(input_path: Path, input_format: str | None) -> str:
    fmt = (input_format or "auto").lower()
    if fmt not in SUPPORTED_FORMATS:
        fail(f"input_format must be one of {sorted(SUPPORTED_FORMATS)}.")
    if fmt != "auto":
        return fmt

    suffix = input_path.suffix.lower()
    mapping = {
        ".csv": "csv",
        ".xlsx": "xlsx",
        ".xls": "xls",
        ".tsv": "tsv",
        ".txt": "txt",
    }
    detected = mapping.get(suffix)
    if not detected:
        fail(f"Could not detect input format from suffix '{suffix}'.")
    return detected


def read_dataframe(input_path: Path, detected_format: str, sheet_name: str | int | None):
    try:
        import pandas as pd
    except ModuleNotFoundError:
        fail("Please install pandas: py -m pip install pandas")

    if detected_format == "csv":
        return pd.read_csv(input_path)
    if detected_format == "xlsx":
        return pd.read_excel(input_path, sheet_name=sheet_name or 0, engine="openpyxl")
    if detected_format == "tsv":
        return pd.read_csv(input_path, sep="\t")
    if detected_format == "txt":
        return pd.read_csv(input_path, sep=None, engine="python")
    if detected_format == "xls":
        fail("XLS input requires xlrd and is not part of the v0.2 acceptance path.")
    fail(f"Unsupported detected format: {detected_format}")


def validate_config(config: dict[str, Any]) -> tuple[dict[str, Any], Any]:
    required = ["input_file", "x_column", "y_columns", "graph_type", "output_dir", "output_basename"]
    for key in required:
        if key not in config or config[key] in (None, ""):
            fail(f"Missing required field: {key}")

    y_columns = config["y_columns"]
    if not isinstance(y_columns, list) or not y_columns:
        fail("y_columns must be a non-empty list.")
    if not all(isinstance(col, str) and col for col in y_columns):
        fail("Every y_columns entry must be a non-empty string.")

    graph_type = str(config["graph_type"]).lower()
    if graph_type not in SUPPORTED_GRAPH_TYPES:
        fail(f"graph_type must be one of {sorted(SUPPORTED_GRAPH_TYPES)}.")

    style_profile_path, style_profile = load_optional_profile(config, "style_profile")
    export_profile_path, export_profile = load_optional_profile(config, "export_profile")
    export_settings = effective_export_settings(config, style_profile, export_profile)

    input_path = resolve_project_path(str(config["input_file"]))
    if not input_path.exists():
        fail(f"input_file does not exist: {input_path}")

    detected_format = detect_format(input_path, config.get("input_format"))
    df = read_dataframe(input_path, detected_format, config.get("sheet_name"))

    x_column = str(config["x_column"])
    missing = [col for col in [x_column, *y_columns] if col not in df.columns]
    if missing:
        fail(f"Missing column(s): {missing}")

    selected = df[[x_column, *y_columns]].copy()
    for col in selected.columns:
        selected[col] = __import__("pandas").to_numeric(selected[col], errors="coerce")
    valid = selected.dropna()
    if len(valid) < 2:
        fail("Selected x/y columns must contain at least 2 valid numeric rows.")
    y_error_columns, x_error_column, errorbar_warnings = validate_errorbar_columns(config, df, y_columns)

    summary = {
        "input_file": str(config["input_file"]),
        "detected_format": detected_format,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "x_column": x_column,
        "y_columns": y_columns,
        "graph_type": graph_type,
        "style_profile": style_profile_path,
        "export_profile": export_profile_path,
        "effective_export_settings": export_settings,
        "y_error_columns": y_error_columns,
        "x_error_column": x_error_column,
        "errorbar_validation_warnings": errorbar_warnings,
        "output_dir": str(config["output_dir"]),
        "output_basename": str(config["output_basename"]),
    }
    return summary, df


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate origin-plot v0.2 YAML configuration.")
    parser.add_argument("--config", default="configs/origin_plot_config.yaml")
    args = parser.parse_args()

    config_path = resolve_project_path(args.config)
    if not config_path.exists():
        fail(f"Config file does not exist: {config_path}")

    config = load_yaml(config_path)
    summary, _ = validate_config(config)
    print("Config summary:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("PASS: config validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
