"""Smart data understanding for origin-plot v0.9.

Reads a CSV / XLSX / TSV / TXT / Markdown file, detects header row, units,
column roles (x / y / error / group), recommends a graph type, writes a
structured analysis report, and emits a v0.2-compatible single-plot config so
the existing ``origin_plot_from_config.py`` pipeline can render the figure.

This module never calls Origin. It is import-safe so other scripts (notably
``run_smart_plot.py``) can reuse :func:`analyze` directly.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "smart_input_analysis_report.json"
DEFAULT_GENERATED_CONFIG = PROJECT_ROOT / "configs" / "generated" / "smart_generated_plot_config.yaml"
SUPPORTED_FORMATS = {"auto", "csv", "xlsx", "xls", "tsv", "txt", "md"}
EXTENSION_FORMAT = {
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".xls": "xls",
    ".tsv": "tsv",
    ".txt": "txt",
    ".md": "md",
    ".markdown": "md",
}
DEFAULT_ERROR_SUFFIXES = ("_err", "_error", "_uncertainty", "\u8bef\u5dee", "\u6807\u51c6\u5dee")
DEFAULT_X_CANDIDATES = (
    "x",
    "time",
    "\u65f6\u95f4",
    "distance",
    "\u8ddd\u79bb",
    "voltage",
    "\u7535\u538b",
    "wavelength",
    "\u6ce2\u957f",
)
DEFAULT_GROUP_CANDIDATES = ("group", "type", "category", "\u7c7b\u522b", "\u7ec4\u522b")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def current_timestamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise RuntimeError("Please install PyYAML: py -m pip install pyyaml") from exc
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Smart config must be a YAML mapping: {rel(path)}")
    return data


def save_yaml(path: Path, data: dict[str, Any]) -> None:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise RuntimeError("Please install PyYAML: py -m pip install pyyaml") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def detect_format(input_path: Path, declared: str | None) -> str:
    fmt = (declared or "auto").lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"input_format must be one of {sorted(SUPPORTED_FORMATS)}; got {declared!r}"
        )
    if fmt != "auto":
        return fmt
    detected = EXTENSION_FORMAT.get(input_path.suffix.lower())
    if not detected:
        raise ValueError(f"Could not detect input format from suffix '{input_path.suffix}'.")
    return detected


# --- Markdown parsing -----------------------------------------------------

def extract_first_markdown_table(text: str) -> tuple[list[str], list[list[str]]] | None:
    """Return the first standard ``| ... |`` Markdown table as (headers, rows)."""
    lines = text.splitlines()
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        if "|" in line and line.strip().startswith("|"):
            # Possible header row. Need a separator line of dashes next.
            if i + 1 < n and re.search(r"^\s*\|?\s*[:\-\s|]+\|", lines[i + 1]):
                header_cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                rows: list[list[str]] = []
                j = i + 2
                while j < n and "|" in lines[j] and lines[j].strip().startswith("|"):
                    row_cells = [cell.strip() for cell in lines[j].strip().strip("|").split("|")]
                    rows.append(row_cells)
                    j += 1
                if header_cells and rows:
                    return header_cells, rows
        i += 1
    return None


def markdown_to_dataframe(input_path: Path):
    import pandas as pd

    text = input_path.read_text(encoding="utf-8")
    table = extract_first_markdown_table(text)
    if table is None:
        raise ValueError(
            f"No Markdown table found in {rel(input_path)}; expected pipe-formatted table."
        )
    headers, rows = table
    width = len(headers)
    cleaned_rows = [
        (row + [""] * (width - len(row)))[:width] for row in rows
    ]
    df = pd.DataFrame(cleaned_rows, columns=headers)
    for col in df.columns:
        coerced = pd.to_numeric(df[col], errors="coerce")
        if coerced.notna().sum() >= max(1, len(df) // 2):
            df[col] = coerced
    return df


# --- Excel sheet selection ------------------------------------------------

def read_excel_with_auto_sheet(input_path: Path, sheet_name: Any | None, auto_select: bool) -> tuple[Any, str | None]:
    import pandas as pd

    if sheet_name is not None and sheet_name != "":
        df = pd.read_excel(input_path, sheet_name=sheet_name, engine="openpyxl")
        return df, str(sheet_name)
    if not auto_select:
        df = pd.read_excel(input_path, sheet_name=0, engine="openpyxl")
        return df, None

    book = pd.ExcelFile(input_path, engine="openpyxl")
    best: tuple[int, str, Any] | None = None
    for name in book.sheet_names:
        candidate = book.parse(name)
        numeric_count = sum(
            1
            for col in candidate.columns
            if pd.to_numeric(candidate[col], errors="coerce").notna().any()
        )
        score = numeric_count
        if best is None or score > best[0]:
            best = (score, name, candidate)
    if best is None:
        raise ValueError(f"No readable sheet in {rel(input_path)}")
    return best[2], best[1]


# --- DataFrame loading ----------------------------------------------------

def read_dataframe(input_path: Path, detected_format: str, smart_cfg: dict[str, Any], cfg: dict[str, Any]):
    import pandas as pd

    if detected_format == "csv":
        return pd.read_csv(input_path), None
    if detected_format == "tsv":
        return pd.read_csv(input_path, sep="\t"), None
    if detected_format == "txt":
        return pd.read_csv(input_path, sep=None, engine="python"), None
    if detected_format == "xlsx":
        excel_cfg = cfg.get("excel") or {}
        auto_select = bool(excel_cfg.get("auto_detect_sheet", True))
        df, sheet = read_excel_with_auto_sheet(input_path, cfg.get("sheet_name"), auto_select)
        return df, sheet
    if detected_format == "xls":
        raise ValueError("XLS input requires xlrd; not part of v0.9 smart-input support.")
    if detected_format == "md":
        markdown_cfg = cfg.get("markdown") or {}
        if not bool(markdown_cfg.get("extract_first_table", True)):
            raise ValueError("Markdown input requires markdown.extract_first_table=true.")
        return markdown_to_dataframe(input_path), None
    raise ValueError(f"Unsupported detected format: {detected_format}")


# --- Column analysis ------------------------------------------------------

UNIT_PATTERN = re.compile(r"^(?P<name>.*?)[\s_]*[\(\[](?P<unit>[^\)\]]+)[\)\]]\s*$")


def split_column_unit(column: str) -> tuple[str, str | None]:
    match = UNIT_PATTERN.match(column)
    if not match:
        return column, None
    return match.group("name").strip(), match.group("unit").strip()


def detect_columns(df, role_rules: dict[str, Any]) -> dict[str, Any]:
    import pandas as pd

    column_names: list[str] = [str(col) for col in df.columns]
    units: dict[str, str] = {}
    numeric_columns: list[str] = []
    text_columns: list[str] = []
    for col in column_names:
        _, unit = split_column_unit(col)
        if unit:
            units[col] = unit
        series_numeric = pd.to_numeric(df[col], errors="coerce")
        if series_numeric.notna().any() and series_numeric.notna().sum() >= max(1, len(df) // 2):
            numeric_columns.append(col)
        else:
            text_columns.append(col)
    return {
        "column_names": column_names,
        "units": units,
        "numeric_columns": numeric_columns,
        "text_columns": text_columns,
    }


def normalize_token(value: str) -> str:
    return value.strip().lower()


def find_x_candidates(numeric_columns: list[str], rules: dict[str, Any]) -> list[str]:
    explicit = list(rules.get("x_column_candidates") or DEFAULT_X_CANDIDATES)
    matches: list[str] = []
    for col in numeric_columns:
        name = split_column_unit(col)[0]
        token = normalize_token(name)
        for candidate in explicit:
            if normalize_token(str(candidate)) == token:
                matches.append(col)
                break
    return matches


def find_error_columns(
    numeric_columns: list[str], rules: dict[str, Any]
) -> dict[str, str]:
    suffixes = list(rules.get("error_column_suffixes") or DEFAULT_ERROR_SUFFIXES)
    mapping: dict[str, str] = {}
    if not bool(rules.get("infer_error_columns_by_suffix", True)):
        return mapping
    for col in numeric_columns:
        name = split_column_unit(col)[0]
        lower = normalize_token(name)
        for suffix in suffixes:
            if not suffix:
                continue
            suffix_norm = normalize_token(str(suffix))
            if lower.endswith(suffix_norm):
                base = name[: len(name) - len(suffix)]
                base = base.rstrip("_-")
                # Map to an existing y candidate by base name (case-insensitive).
                for candidate in numeric_columns:
                    candidate_name = split_column_unit(candidate)[0]
                    if normalize_token(candidate_name) == normalize_token(base):
                        mapping[candidate] = col
                        break
    return mapping


def find_group_columns(
    text_columns: list[str], rules: dict[str, Any]
) -> list[str]:
    if not bool(rules.get("infer_group_columns_by_text", True)):
        return []
    explicit = list(rules.get("group_column_candidates") or DEFAULT_GROUP_CANDIDATES)
    explicit_norm = {normalize_token(str(c)) for c in explicit}
    matches: list[str] = []
    for col in text_columns:
        name = split_column_unit(col)[0]
        if normalize_token(name) in explicit_norm:
            matches.append(col)
    if matches:
        return matches
    # Fall back to any text column that has at least 2 unique values.
    return list(text_columns)


def select_roles(
    df,
    column_info: dict[str, Any],
    role_rules: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    numeric_columns = list(column_info["numeric_columns"])
    text_columns = list(column_info["text_columns"])

    # X column.
    x_candidates = find_x_candidates(numeric_columns, role_rules)
    if x_candidates:
        x_column = x_candidates[0]
    elif role_rules.get("prefer_first_numeric_as_x", True) and numeric_columns:
        x_column = numeric_columns[0]
    else:
        x_column = None
        warnings.append("could not infer x column; no numeric columns available")

    # Error columns.
    error_columns_full = find_error_columns(numeric_columns, role_rules)

    # Group columns.
    group_candidates = find_group_columns(text_columns, role_rules)
    group_column = group_candidates[0] if group_candidates else None

    # Y columns: numeric columns excluding x and any errors.
    error_targets = set(error_columns_full.values())
    y_columns = [
        col for col in numeric_columns
        if col != x_column and col not in error_targets
    ]
    # Restrict error mapping to selected y columns.
    error_columns = {y: error_columns_full[y] for y in y_columns if y in error_columns_full}

    if not y_columns and group_column is not None and numeric_columns:
        # grouped value layout: x present, group + value
        y_columns = [col for col in numeric_columns if col != x_column]

    if not y_columns:
        warnings.append("could not infer any y column; downstream plot will be skipped")

    role_candidates = {
        "x": x_candidates,
        "y": y_columns,
        "y_error": list(error_columns.keys()),
        "group": group_candidates,
    }
    selected = {
        "x_column": x_column,
        "y_columns": y_columns,
        "y_error_columns": error_columns,
        "group_column": group_column,
    }
    return {"role_candidates": role_candidates, "selected_roles": selected, "warnings": warnings}, warnings


def recommend_graph_type(roles: dict[str, Any], column_info: dict[str, Any]) -> tuple[str, list[str]]:
    warnings: list[str] = []
    selected = roles["selected_roles"]
    y_columns = selected.get("y_columns") or []
    error_map = selected.get("y_error_columns") or {}
    group_column = selected.get("group_column")
    x_column = selected.get("x_column")

    if not x_column or not y_columns:
        warnings.append(
            "missing x or y; falling back to scatter to avoid claiming a stronger plot type"
        )
        return "scatter", warnings

    if error_map:
        return "errorbar", warnings

    if group_column:
        return "grouped_line", warnings

    return "line", warnings


# --- Generated plot config ------------------------------------------------

def derive_basename(input_path: Path, override: str | None) -> str:
    if override:
        return str(override)
    stem = input_path.stem
    safe = re.sub(r"[^A-Za-z0-9_\-]+", "_", stem).strip("_")
    if not safe:
        safe = "smart_plot"
    return f"smart_{safe}"


def build_plot_config(
    input_path: Path,
    detected_format: str,
    sheet_name: str | None,
    column_info: dict[str, Any],
    selected_roles: dict[str, Any],
    graph_type: str,
    cfg: dict[str, Any],
    basename: str,
    output_dir: Path,
) -> dict[str, Any]:
    output_cfg = cfg.get("output") or {}
    style_profile = output_cfg.get("style_profile")
    export_profile = output_cfg.get("export_profile")

    units = column_info["units"]

    x_column = selected_roles["x_column"]
    y_columns = list(selected_roles["y_columns"])
    error_columns = dict(selected_roles.get("y_error_columns") or {})
    group_column = selected_roles.get("group_column")

    x_title_default = x_column or ""
    if x_column and x_column in units:
        x_title_default = f"{split_column_unit(x_column)[0]} ({units[x_column]})"
    y_title_default = ", ".join(y_columns) if y_columns else ""

    plot_cfg: dict[str, Any] = {
        "input_file": rel(input_path).replace("\\", "/"),
        "input_format": detected_format,
        "sheet_name": sheet_name,
        "x_column": x_column,
        "y_columns": y_columns,
        "y_error_columns": error_columns or None,
        "x_error_column": None,
        "graph_type": graph_type,
        "graph_title": f"Smart auto plot: {input_path.name}",
        "x_title": x_title_default,
        "y_title": y_title_default,
        "style_profile": style_profile,
        "export_profile": export_profile,
        "output_dir": rel(output_dir).replace("\\", "/"),
        "output_basename": basename,
        "show_origin": bool(output_cfg.get("show_origin", True)),
    }
    if group_column and graph_type in {"grouped_line", "grouped_scatter"}:
        plot_cfg["group_column"] = group_column
    if not plot_cfg["y_error_columns"]:
        plot_cfg.pop("y_error_columns")
    return plot_cfg


# --- Public entry point ---------------------------------------------------

def analyze(cfg: dict[str, Any]) -> dict[str, Any]:
    """Run smart analysis and emit a generated plot config + analysis report.

    Returns the analysis report as a dict (also persisted to disk).
    """
    smart_section = cfg.get("smart_analysis") or {}
    if not bool(smart_section.get("enabled", True)):
        raise ValueError("smart_analysis.enabled must be true to run analyze().")

    role_rules = cfg.get("role_inference_rules") or {}
    output_cfg = cfg.get("output") or {}

    input_value = cfg.get("input_file")
    if not input_value:
        raise ValueError("input_file is required.")
    input_path = resolve_project_path(str(input_value))
    if not input_path.exists():
        raise FileNotFoundError(f"input_file does not exist: {rel(input_path)}")

    detected_format = detect_format(input_path, str(cfg.get("input_format", "auto")))
    df, sheet_name = read_dataframe(input_path, detected_format, smart_section, cfg)

    warnings: list[str] = []
    if df.empty:
        raise ValueError(f"input file produced an empty dataframe: {rel(input_path)}")
    column_info = detect_columns(df, role_rules)
    if not column_info["column_names"]:
        raise ValueError(f"no columns detected in {rel(input_path)}")

    role_result, role_warnings = select_roles(df, column_info, role_rules)
    warnings.extend(role_warnings)
    graph_type, gtype_warnings = recommend_graph_type(role_result, column_info)
    warnings.extend(gtype_warnings)

    selected_roles = role_result["selected_roles"]
    has_y = bool(selected_roles.get("y_columns"))
    status = "PASS" if has_y else "PARTIAL PASS"

    basename = derive_basename(
        input_path, output_cfg.get("output_basename")
    )
    output_dir_value = output_cfg.get("output_dir") or "output/origin_plot_smart"
    output_dir = resolve_project_path(str(output_dir_value)) / basename

    # Markdown is not natively supported by the v0.2 plotting pipeline.
    # Persist a CSV bridge so origin_plot_from_config.py can consume it as csv.
    plot_input_path = input_path
    plot_input_format = detected_format
    if detected_format == "md":
        bridge_dir = PROJECT_ROOT / "data" / "smart_inputs" / "_bridges"
        bridge_dir.mkdir(parents=True, exist_ok=True)
        bridge_path = bridge_dir / f"{basename}.csv"
        df.to_csv(bridge_path, index=False, encoding="utf-8")
        plot_input_path = bridge_path
        plot_input_format = "csv"
        warnings.append(
            f"markdown converted to CSV bridge: {rel(bridge_path)}"
        )

    plot_cfg = build_plot_config(
        plot_input_path,
        plot_input_format,
        sheet_name,
        column_info,
        selected_roles,
        graph_type,
        cfg,
        basename,
        output_dir,
    )

    generated_config_path_value = output_cfg.get(
        "generated_config_path", str(rel(DEFAULT_GENERATED_CONFIG))
    )
    if Path(generated_config_path_value).is_absolute():
        raise ValueError("output.generated_config_path must be relative")
    generated_config_path = resolve_project_path(str(generated_config_path_value))
    save_yaml(generated_config_path, plot_cfg)

    smart_report_path_value = output_cfg.get(
        "smart_report_path", str(rel(DEFAULT_REPORT_PATH))
    )
    if Path(smart_report_path_value).is_absolute():
        raise ValueError("output.smart_report_path must be relative")
    smart_report_path = resolve_project_path(str(smart_report_path_value))

    report = {
        "timestamp_utc": current_timestamp_utc(),
        "status": status,
        "input_file": rel(input_path),
        "detected_format": detected_format,
        "sheet_name": sheet_name,
        "header_row": 0,
        "column_names": column_info["column_names"],
        "units": column_info["units"],
        "numeric_columns": column_info["numeric_columns"],
        "text_columns": column_info["text_columns"],
        "role_candidates": role_result["role_candidates"],
        "selected_roles": selected_roles,
        "recommended_graph_type": graph_type,
        "generated_plot_config": rel(generated_config_path),
        "plot_input_path": rel(plot_input_path),
        "plot_input_format": plot_input_format,
        "warnings": warnings,
        "errors": [],
    }
    smart_report_path.parent.mkdir(parents=True, exist_ok=True)
    smart_report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a smart input file and emit an origin-plot config."
    )
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

    config_path = resolve_project_path(args.config)
    if not config_path.exists():
        print(f"FAIL: smart config does not exist: {rel(config_path)}")
        return 1

    cfg = load_yaml(config_path)
    if args.input_file:
        cfg["input_file"] = args.input_file
    try:
        report = analyze(cfg)
    except Exception as exc:  # noqa: BLE001 - smart input must surface failure
        print(f"FAIL: smart analysis failed: {type(exc).__name__}: {exc}")
        return 1

    print(f"status: {report['status']}")
    print(f"input_file: {report['input_file']}")
    print(f"recommended_graph_type: {report['recommended_graph_type']}")
    print(f"generated_plot_config: {report['generated_plot_config']}")
    return 0 if report["status"] in {"PASS", "PARTIAL PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
