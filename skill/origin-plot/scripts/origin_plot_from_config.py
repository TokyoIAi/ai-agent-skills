from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "origin_plot_v0_2_report.json"
SUPPORTED_GRAPH_TYPES = {"line", "scatter", "line_symbol"}
SUPPORTED_FORMATS = {"auto", "csv", "xlsx", "xls", "tsv", "txt"}
EXPORT_KEYS = ("export_png", "export_pdf", "save_opju", "png_width")
MANUAL_INTERVENTION = {
    "user_reported_manual_ok": True,
    "current_rerun_popup_observed_by_user": False,
    "manual_intervention_required": "first_run_only",
    "notes": (
        "User reported one manual OK during initial validation. A later PowerShell rerun "
        "completed without a popup. GUI dialog auto-clicking is intentionally not implemented."
    ),
}


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


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ModuleNotFoundError:
        raise RuntimeError("Please install PyYAML: py -m pip install pyyaml") from None

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError("Config must be a YAML mapping.")
    return data


def load_optional_profile(config: dict[str, Any], key: str) -> tuple[str | None, dict[str, Any]]:
    value = config.get(key)
    if not value:
        return None, {}
    path = resolve_project_path(str(value))
    if not path.exists():
        raise FileNotFoundError(f"{key} does not exist: {path}")
    return rel(path), load_yaml(path)


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
    settings["png_width"] = int(settings["png_width"] or 0)
    return settings


def style_settings(style_profile: dict[str, Any]) -> dict[str, Any]:
    graph = style_profile.get("graph", {}) if isinstance(style_profile, dict) else {}
    axis = style_profile.get("axis", {}) if isinstance(style_profile, dict) else {}
    line = style_profile.get("line", {}) if isinstance(style_profile, dict) else {}
    return {
        "title_enabled": bool(graph.get("title_enabled", True)),
        "legend_enabled": bool(graph.get("legend_enabled", True)),
        "rescale": bool(graph.get("rescale", True)),
        "x_title_enabled": bool(axis.get("x_title_enabled", True)),
        "y_title_enabled": bool(axis.get("y_title_enabled", True)),
        "line_width": line.get("width"),
        "symbol_size": line.get("symbol_size"),
    }


def build_effective_config(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    style_profile_path, style_profile = load_optional_profile(config, "style_profile")
    export_profile_path, export_profile = load_optional_profile(config, "export_profile")
    export_settings = effective_export_settings(config, style_profile, export_profile)
    effective = dict(config)
    effective.update(export_settings)
    style_info = {
        "style_profile": style_profile_path,
        "export_profile": export_profile_path,
        "effective_export_settings": export_settings,
        "applied_style_features": [],
        "style_warnings": [],
    }
    return effective, style_settings(style_profile), style_info


def detect_format(input_path: Path, input_format: str | None) -> str:
    fmt = (input_format or "auto").lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"input_format must be one of {sorted(SUPPORTED_FORMATS)}.")
    if fmt != "auto":
        return fmt
    mapping = {
        ".csv": "csv",
        ".xlsx": "xlsx",
        ".xls": "xls",
        ".tsv": "tsv",
        ".txt": "txt",
    }
    detected = mapping.get(input_path.suffix.lower())
    if not detected:
        raise ValueError(f"Could not detect input format from suffix '{input_path.suffix}'.")
    return detected


def read_dataframe(input_path: Path, detected_format: str, sheet_name: str | int | None):
    import pandas as pd

    if detected_format == "csv":
        return pd.read_csv(input_path)
    if detected_format == "xlsx":
        return pd.read_excel(input_path, sheet_name=sheet_name or 0, engine="openpyxl")
    if detected_format == "tsv":
        return pd.read_csv(input_path, sep="\t")
    if detected_format == "txt":
        return pd.read_csv(input_path, sep=None, engine="python")
    if detected_format == "xls":
        raise RuntimeError("XLS input requires xlrd and is not part of the v0.2 acceptance path.")
    raise ValueError(f"Unsupported detected format: {detected_format}")


def requested_outputs(config: dict[str, Any], output_dir: Path, basename: str) -> dict[str, Path | None]:
    return {
        "png": output_dir / f"{basename}.png" if config.get("export_png", True) else None,
        "pdf": output_dir / f"{basename}.pdf" if config.get("export_pdf", True) else None,
        "opju": output_dir / f"{basename}.opju" if config.get("save_opju", True) else None,
    }


def output_status(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"path": None, "exists": False, "size_bytes": 0}
    exists = path.exists()
    return {
        "path": rel(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
    }


def build_report(
    status: str,
    config_path: Path,
    input_file: Path | None,
    detected_format: str | None,
    row_count_raw: int,
    row_count_used: int,
    x_column: str | None,
    y_columns: list[str],
    graph_type: str | None,
    outputs: dict[str, Path | None],
    style: dict[str, Any],
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any]:
    return {
        "status": status,
        "config_path": rel(config_path),
        "input_file": rel(input_file) if input_file else None,
        "detected_format": detected_format,
        "row_count_raw": row_count_raw,
        "row_count_used": row_count_used,
        "x_column": x_column,
        "y_columns": y_columns,
        "graph_type": graph_type,
        "outputs": {name: output_status(path) for name, path in outputs.items()},
        "style": style,
        "manual_intervention": MANUAL_INTERVENTION,
        "warnings": warnings,
        "errors": errors,
    }


def save_report(report: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report: {rel(REPORT_PATH)}")


def prepare_data(config: dict[str, Any]):
    import pandas as pd

    required = ["input_file", "x_column", "y_columns", "graph_type", "output_dir", "output_basename"]
    for key in required:
        if key not in config or config[key] in (None, ""):
            raise ValueError(f"Missing required field: {key}")

    y_columns = config["y_columns"]
    if not isinstance(y_columns, list) or not y_columns:
        raise ValueError("y_columns must be a non-empty list.")
    y_columns = [str(col) for col in y_columns]

    graph_type = str(config["graph_type"]).lower()
    if graph_type not in SUPPORTED_GRAPH_TYPES:
        raise ValueError(f"graph_type must be one of {sorted(SUPPORTED_GRAPH_TYPES)}.")

    input_path = resolve_project_path(str(config["input_file"]))
    if not input_path.exists():
        raise FileNotFoundError(f"input_file does not exist: {input_path}")

    detected_format = detect_format(input_path, config.get("input_format"))
    df = read_dataframe(input_path, detected_format, config.get("sheet_name"))

    x_column = str(config["x_column"])
    missing = [col for col in [x_column, *y_columns] if col not in df.columns]
    if missing:
        raise ValueError(f"Missing column(s): {missing}")

    plot_df = df[[x_column, *y_columns]].copy()
    for col in plot_df.columns:
        plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce")
    row_count_raw = int(len(plot_df))
    plot_df = plot_df.dropna()
    row_count_used = int(len(plot_df))
    dropped = row_count_raw - row_count_used
    if row_count_used < 2:
        raise ValueError("Selected x/y columns must contain at least 2 valid numeric rows.")
    return input_path, detected_format, df, plot_df, x_column, y_columns, graph_type, dropped


def graph_template_and_plot_type(graph_type: str, warnings: list[str]) -> tuple[str, str]:
    if graph_type == "line":
        return "line", "l"
    if graph_type == "scatter":
        return "scatter", "s"
    if graph_type == "line_symbol":
        return "line", "y"
    warnings.append(f"Unsupported graph_type {graph_type}; fallback to line.")
    return "line", "l"


def apply_plot_style(plot: Any, settings: dict[str, Any], style_info: dict[str, Any]) -> None:
    line_width = settings.get("line_width")
    if line_width is not None:
        try:
            plot.width = int(line_width)
            style_info["applied_style_features"].append("line.width")
        except Exception as exc:  # noqa: BLE001 - style support varies by Origin plot type
            style_info["style_warnings"].append(f"Could not apply line.width: {type(exc).__name__}: {exc}")

    symbol_size = settings.get("symbol_size")
    if symbol_size is not None:
        try:
            plot.symbol_size = int(symbol_size)
            style_info["applied_style_features"].append("line.symbol_size")
        except Exception as exc:  # noqa: BLE001 - style support varies by Origin plot type
            style_info["style_warnings"].append(f"Could not apply line.symbol_size: {type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Origin plot from v0.2 YAML configuration.")
    parser.add_argument("--config", default="configs/origin_plot_config.yaml")
    args = parser.parse_args()

    config_path = resolve_project_path(args.config)
    warnings: list[str] = []
    errors: list[str] = []
    outputs: dict[str, Path | None] = {"png": None, "pdf": None, "opju": None}
    input_path: Path | None = None
    detected_format: str | None = None
    row_count_raw = 0
    row_count_used = 0
    x_column: str | None = None
    y_columns: list[str] = []
    graph_type: str | None = None
    style_info: dict[str, Any] = {
        "style_profile": None,
        "export_profile": None,
        "effective_export_settings": {},
        "applied_style_features": [],
        "style_warnings": [],
    }
    settings: dict[str, Any] = style_settings({})
    op = None

    try:
        config = load_yaml(config_path)
        effective_config, settings, style_info = build_effective_config(config)
        input_path, detected_format, raw_df, plot_df, x_column, y_columns, graph_type, dropped = prepare_data(effective_config)
        row_count_raw = int(len(raw_df))
        row_count_used = int(len(plot_df))
        if dropped:
            warning = f"Dropped {dropped} row(s) with NaN after numeric conversion."
            warnings.append(warning)
            print(warning)

        output_dir = resolve_project_path(str(effective_config["output_dir"]))
        basename = str(effective_config["output_basename"])
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs = requested_outputs(effective_config, output_dir, basename)

        import originpro as op  # type: ignore

        try:
            op.set_show(bool(effective_config.get("show_origin", True)))
        except Exception:
            print("FAIL: op.set_show failed")
            traceback.print_exc()
            raise

        wks = op.new_sheet()
        wks.from_df(plot_df)
        try:
            wks.cols_axis("X" + "Y" * len(y_columns))
        except Exception as exc:  # noqa: BLE001 - non-critical axis role metadata
            warnings.append(f"Could not set worksheet column axis metadata: {type(exc).__name__}: {exc}")

        template, plot_type = graph_template_and_plot_type(graph_type, warnings)
        try:
            graph = op.new_graph(template=template)
        except Exception as exc:  # noqa: BLE001 - fallback keeps requested plot moving
            warnings.append(
                f"Could not create graph template '{template}' ({type(exc).__name__}: {exc}); fallback to line."
            )
            graph = op.new_graph(template="line")
            plot_type = "l"

        layer = graph[0]
        for y_index, y_col in enumerate(y_columns, start=1):
            plot = layer.add_plot(wks, coly=y_index, colx=0, type=plot_type)
            if plot is None and plot_type != "l":
                warnings.append(f"{graph_type} plot type was not accepted for {y_col}; fallback to line.")
                plot = layer.add_plot(wks, coly=y_index, colx=0, type="l")
            if plot is None:
                raise RuntimeError(f"Origin did not create plot for Y column: {y_col}")
            try:
                plot.name = str(y_col)
            except Exception:
                pass
            apply_plot_style(plot, settings, style_info)

        title = str(effective_config.get("graph_title") or input_path.name)
        if settings.get("title_enabled", True):
            try:
                graph.lt_exec(f'title.text$ = "{title}";')
                style_info["applied_style_features"].append("graph.title")
            except Exception as exc:  # noqa: BLE001 - title is cosmetic, plot can still export
                style_info["style_warnings"].append(f"Could not set graph title: {type(exc).__name__}: {exc}")
        else:
            style_info["applied_style_features"].append("graph.title_disabled")

        try:
            if settings.get("x_title_enabled", True):
                layer.axis("x").title = str(effective_config.get("x_title") or x_column)
                style_info["applied_style_features"].append("axis.x_title")
            if settings.get("y_title_enabled", True):
                layer.axis("y").title = str(effective_config.get("y_title") or ", ".join(y_columns))
                style_info["applied_style_features"].append("axis.y_title")
        except Exception as exc:  # noqa: BLE001 - labels are reported but not fatal
            style_info["style_warnings"].append(f"Could not set axis title(s): {type(exc).__name__}: {exc}")

        if settings.get("legend_enabled", True):
            try:
                graph.lt_exec("legend -r;")
                style_info["applied_style_features"].append("graph.legend")
            except Exception as exc:  # noqa: BLE001 - legend is reported but not fatal
                style_info["style_warnings"].append(f"Could not refresh legend: {type(exc).__name__}: {exc}")
        else:
            try:
                graph.lt_exec("legend -d;")
                style_info["applied_style_features"].append("graph.legend_disabled")
            except Exception as exc:  # noqa: BLE001 - legend removal support varies
                style_info["style_warnings"].append(f"Could not disable legend: {type(exc).__name__}: {exc}")

        if settings.get("rescale", True):
            layer.rescale()
            style_info["applied_style_features"].append("graph.rescale")

        if outputs["png"] is not None:
            graph.save_fig(str(outputs["png"]), width=int(effective_config.get("png_width") or 0))
        if outputs["pdf"] is not None:
            graph.save_fig(str(outputs["pdf"]))
        if outputs["opju"] is not None:
            op.save(str(outputs["opju"]))

        missing = [name for name, path in outputs.items() if path is not None and not path.exists()]
        status = "PASS" if not missing else "PARTIAL PASS"
        if missing:
            errors.append(f"Missing requested outputs: {missing}")
            print("FAIL: missing requested Origin outputs:")
            for name in missing:
                print(f"- {name}: {outputs[name]}")
        else:
            print("PASS: generated all requested Origin outputs")

        report = build_report(
            status,
            config_path,
            input_path,
            detected_format,
            row_count_raw,
            row_count_used,
            x_column,
            y_columns,
            graph_type,
            outputs,
            style_info,
            warnings,
            errors,
        )
        save_report(report)
        return 0 if status == "PASS" else 1

    except Exception as exc:  # noqa: BLE001 - print full traceback for automation failures
        errors.append(f"{type(exc).__name__}: {exc}")
        traceback.print_exc()
        report = build_report(
            "FAIL",
            config_path,
            input_path,
            detected_format,
            row_count_raw,
            row_count_used,
            x_column,
            y_columns,
            graph_type,
            outputs,
            style_info,
            warnings,
            errors,
        )
        save_report(report)
        return 1
    finally:
        if op is not None:
            try:
                op.exit()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
