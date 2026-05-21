from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_GRAPH_TYPES = {"line", "scatter", "line_symbol"}
SUPPORTED_FORMATS = {"auto", "csv", "xlsx", "xls", "tsv", "txt"}


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

    summary = {
        "input_file": str(config["input_file"]),
        "detected_format": detected_format,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "x_column": x_column,
        "y_columns": y_columns,
        "graph_type": graph_type,
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
