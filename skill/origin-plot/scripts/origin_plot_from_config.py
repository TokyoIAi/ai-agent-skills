from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "origin_plot_v0_2_report.json"
SUPPORTED_GRAPH_TYPES = {"line", "scatter", "line_symbol", "errorbar"}
SUPPORTED_FORMATS = {"auto", "csv", "xlsx", "xls", "tsv", "txt"}
EXPORT_KEYS = ("export_png", "export_pdf", "save_opju", "png_width")
SUPPORTED_FIT_MODELS = {"linear", "polynomial"}
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


def normalize_errorbar_config(config: dict[str, Any], y_columns: list[str]) -> tuple[dict[str, str], str | None, list[str]]:
    warnings: list[str] = []
    y_error_columns = config.get("y_error_columns") or {}
    x_error_column = config.get("x_error_column")
    if str(config.get("graph_type", "")).lower() == "errorbar" and not y_error_columns:
        warnings.append("graph_type=errorbar but y_error_columns is missing; ordinary plot fallback is expected.")
    if y_error_columns and not isinstance(y_error_columns, dict):
        raise ValueError("y_error_columns must be a mapping from Y column to error column.")

    normalized_y_errors: dict[str, str] = {}
    for y_col, err_col in y_error_columns.items():
        y_col = str(y_col)
        err_col = str(err_col)
        if y_col not in y_columns:
            raise ValueError(f"y_error_columns key must be one of y_columns: {y_col}")
        normalized_y_errors[y_col] = err_col
    return normalized_y_errors, str(x_error_column) if x_error_column not in (None, "") else None, warnings


def normalize_fit_config(config: dict[str, Any], y_columns: list[str]) -> tuple[bool, list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    fitting = config.get("fitting") or {}
    if not isinstance(fitting, dict):
        raise ValueError("fitting must be a mapping.")
    enabled = bool(fitting.get("enabled", False))
    if not enabled:
        return False, [], warnings
    models = fitting.get("models")
    if not isinstance(models, list) or not models:
        raise ValueError("fitting.enabled=true requires a non-empty models list.")

    seen_names: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for item in models:
        if not isinstance(item, dict):
            raise ValueError("Each fitting model entry must be a mapping.")
        name = str(item.get("name") or "")
        if not name:
            raise ValueError("Each fitting model must include name.")
        if name in seen_names:
            raise ValueError(f"Fitting model names must be unique: {name}")
        seen_names.add(name)
        y_column = str(item.get("y_column") or "")
        if y_column not in y_columns:
            raise ValueError(f"Fitting y_column must belong to y_columns: {y_column}")
        model = str(item.get("model") or "").lower()
        if model not in SUPPORTED_FIT_MODELS:
            warnings.append(f"Unsupported fitting model requested: {model}")
            continue
        degree = 1
        if model == "polynomial":
            degree = int(item.get("degree"))
            if degree < 2 or degree > 5:
                raise ValueError("Polynomial degree must be an integer from 2 to 5.")
        points = int(item.get("output_curve_points", 100))
        if points < 20 or points > 1000:
            raise ValueError("output_curve_points must be between 20 and 1000.")
        normalized.append(
            {
                "name": name,
                "y_column": y_column,
                "model": model,
                "degree": degree,
                "output_curve_points": points,
                "show_equation": bool(item.get("show_equation", True)),
                "show_r_squared": bool(item.get("show_r_squared", True)),
            }
        )
    return enabled, normalized, warnings


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
    errorbar: dict[str, Any],
    fitting: dict[str, Any],
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
        "errorbar": errorbar,
        "fitting": fitting,
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

    y_error_columns, x_error_column, errorbar_warnings = normalize_errorbar_config(config, y_columns)
    extra_columns = list(y_error_columns.values())
    if x_error_column:
        extra_columns.append(x_error_column)
    missing_error_columns = [col for col in extra_columns if col not in df.columns]
    if missing_error_columns:
        raise ValueError(f"Missing error column(s): {missing_error_columns}")

    plot_columns = list(dict.fromkeys([x_column, *y_columns, *extra_columns]))
    plot_df = df[plot_columns].copy()
    for col in plot_df.columns:
        plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce")
    for col in extra_columns:
        if (plot_df[col].dropna() < 0).any():
            raise ValueError(f"Error column contains negative values: {col}")
    row_count_raw = int(len(plot_df))
    plot_df = plot_df.dropna()
    row_count_used = int(len(plot_df))
    dropped = row_count_raw - row_count_used
    if row_count_used < 2:
        raise ValueError("Selected x/y columns must contain at least 2 valid numeric rows.")
    return input_path, detected_format, df, plot_df, x_column, y_columns, graph_type, dropped, y_error_columns, x_error_column, errorbar_warnings


def graph_template_and_plot_type(graph_type: str, warnings: list[str]) -> tuple[str, str]:
    if graph_type == "line":
        return "line", "l"
    if graph_type == "scatter":
        return "scatter", "s"
    if graph_type == "line_symbol":
        return "line", "y"
    if graph_type == "errorbar":
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


def column_index_map(plot_df: Any) -> dict[str, int]:
    return {str(column): index for index, column in enumerate(plot_df.columns)}


def equation_string(coefficients: list[float], model: str, degree: int) -> str:
    if model == "linear":
        return f"y = {coefficients[0]:.6g}*x + {coefficients[1]:.6g}"
    terms: list[str] = []
    for index, coefficient in enumerate(coefficients):
        power = degree - index
        if power == 0:
            terms.append(f"{coefficient:.6g}")
        elif power == 1:
            terms.append(f"{coefficient:.6g}*x")
        else:
            terms.append(f"{coefficient:.6g}*x^{power}")
    return "y = " + " + ".join(terms)


def compute_fit_models(plot_df: Any, x_column: str, fit_models: list[dict[str, Any]], fitting_warnings: list[str]) -> tuple[Any, list[dict[str, Any]]]:
    import numpy as np
    import pandas as pd

    result_df = plot_df.copy()
    results: list[dict[str, Any]] = []
    for model_cfg in fit_models:
        name = model_cfg["name"]
        y_column = model_cfg["y_column"]
        model = model_cfg["model"]
        degree = int(model_cfg["degree"])
        points = int(model_cfg["output_curve_points"])
        model_result = {
            "name": name,
            "y_column": y_column,
            "model": model,
            "degree": degree,
            "coefficients": [],
            "equation": None,
            "r_squared": None,
            "residual_sum_of_squares": None,
            "n_points": 0,
            "curve_added_to_origin": False,
            "warnings": [],
        }
        try:
            valid = pd.DataFrame({"x": plot_df[x_column], "y": plot_df[y_column]}).dropna()
            if len(valid) <= degree + 1:
                raise ValueError("not enough valid data points for requested fit")
            x = valid["x"].to_numpy(dtype=float)
            y = valid["y"].to_numpy(dtype=float)
            coefficients = np.polyfit(x, y, degree)
            y_pred = np.polyval(coefficients, x)
            residuals = y - y_pred
            rss = float(np.sum(residuals**2))
            tss = float(np.sum((y - np.mean(y)) ** 2))
            r_squared = 1.0 if tss == 0 else 1.0 - rss / tss
            x_fit = np.linspace(float(np.min(x)), float(np.max(x)), points)
            y_fit = np.polyval(coefficients, x_fit)
            x_fit_col = f"{name}_x"
            y_fit_col = f"{name}_y"
            fit_df = pd.DataFrame({x_fit_col: x_fit, y_fit_col: y_fit})
            result_df = pd.concat([result_df.reset_index(drop=True), fit_df], axis=1)
            coeff_list = [float(value) for value in coefficients]
            model_result.update(
                {
                    "coefficients": coeff_list,
                    "equation": equation_string(coeff_list, model, degree),
                    "r_squared": float(r_squared),
                    "residual_sum_of_squares": rss,
                    "n_points": int(len(valid)),
                    "fit_x_column": x_fit_col,
                    "fit_y_column": y_fit_col,
                }
            )
        except Exception as exc:  # noqa: BLE001 - record and continue with other models
            warning = f"Fit computation failed for {name}: {type(exc).__name__}: {exc}"
            model_result["warnings"].append(warning)
            fitting_warnings.append(warning)
        results.append(model_result)
    return result_df, results


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
    errorbar_info: dict[str, Any] = {
        "requested": False,
        "applied": False,
        "x_error_column": None,
        "y_error_columns": {},
        "warnings": [],
    }
    fitting_info: dict[str, Any] = {
        "requested": False,
        "applied": False,
        "models": [],
        "warnings": [],
    }
    op = None

    try:
        config = load_yaml(config_path)
        effective_config, settings, style_info = build_effective_config(config)
        (
            input_path,
            detected_format,
            raw_df,
            plot_df,
            x_column,
            y_columns,
            graph_type,
            dropped,
            y_error_columns,
            x_error_column,
            errorbar_warnings,
        ) = prepare_data(effective_config)
        row_count_raw = int(len(raw_df))
        row_count_used = int(len(plot_df))
        fitting_enabled, fit_models, fitting_warnings = normalize_fit_config(effective_config, y_columns)
        plot_df, fit_results = compute_fit_models(plot_df, x_column, fit_models, fitting_warnings)
        fitting_info = {
            "requested": fitting_enabled,
            "applied": False,
            "models": fit_results,
            "warnings": fitting_warnings,
        }
        errorbar_info = {
            "requested": graph_type == "errorbar",
            "applied": False,
            "x_error_column": x_error_column,
            "y_error_columns": y_error_columns,
            "warnings": errorbar_warnings,
        }
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
        col_indices = column_index_map(plot_df)
        errorbar_applied_count = 0
        for y_col in y_columns:
            colyerr = col_indices.get(y_error_columns.get(y_col, ""), -1)
            colxerr = col_indices.get(x_error_column, -1) if x_error_column else -1
            try:
                plot = layer.add_plot(
                    wks,
                    coly=col_indices[y_col],
                    colx=col_indices[x_column],
                    type=plot_type,
                    colyerr=colyerr,
                    colxerr=colxerr,
                )
                if graph_type == "errorbar" and colyerr != -1 and plot is not None:
                    errorbar_applied_count += 1
            except Exception as exc:  # noqa: BLE001 - fallback to ordinary plot and report honestly
                if graph_type == "errorbar":
                    errorbar_info["warnings"].append(
                        f"Could not create errorbar plot for {y_col}; fallback to ordinary plot: {type(exc).__name__}: {exc}"
                    )
                plot = layer.add_plot(wks, coly=col_indices[y_col], colx=col_indices[x_column], type=plot_type)
            if plot is None and plot_type != "l":
                warnings.append(f"{graph_type} plot type was not accepted for {y_col}; fallback to line.")
                plot = layer.add_plot(wks, coly=col_indices[y_col], colx=col_indices[x_column], type="l")
            if plot is None:
                raise RuntimeError(f"Origin did not create plot for Y column: {y_col}")
            try:
                plot.name = str(y_col)
            except Exception:
                pass
            apply_plot_style(plot, settings, style_info)

        fit_curve_added_count = 0
        for model_result in fitting_info["models"]:
            fit_x_column = model_result.get("fit_x_column")
            fit_y_column = model_result.get("fit_y_column")
            if not fit_x_column or not fit_y_column:
                continue
            try:
                fit_plot = layer.add_plot(
                    wks,
                    coly=col_indices[str(fit_y_column)],
                    colx=col_indices[str(fit_x_column)],
                    type="l",
                )
                if fit_plot is None:
                    raise RuntimeError("Origin returned no plot object")
                try:
                    fit_plot.name = str(model_result["name"])
                except Exception:
                    pass
                model_result["curve_added_to_origin"] = True
                fit_curve_added_count += 1
            except Exception as exc:  # noqa: BLE001 - report without failing core plot
                warning = f"Could not add fit curve {model_result['name']} to Origin graph: {type(exc).__name__}: {exc}"
                model_result["warnings"].append(warning)
                fitting_info["warnings"].append(warning)

        if fitting_info["requested"]:
            requested_fit_count = len(fitting_info["models"])
            fitting_info["applied"] = requested_fit_count > 0 and fit_curve_added_count == requested_fit_count
            if requested_fit_count == 0:
                fitting_info["warnings"].append("fitting.enabled=true but no supported fit models were available.")
            elif not fitting_info["applied"]:
                fitting_info["warnings"].append(
                    f"Only added {fit_curve_added_count} of {requested_fit_count} requested fit curve(s) to Origin."
                )

        if graph_type == "errorbar":
            expected_errorbars = len(y_error_columns)
            errorbar_info["applied"] = expected_errorbars > 0 and errorbar_applied_count == expected_errorbars
            if expected_errorbars == 0:
                errorbar_info["warnings"].append("No y_error_columns provided; generated ordinary plot output.")
            elif not errorbar_info["applied"]:
                errorbar_info["warnings"].append(
                    f"Only applied {errorbar_applied_count} of {expected_errorbars} requested Y error column(s)."
                )

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
        if status == "PASS" and errorbar_info["requested"] and not errorbar_info["applied"]:
            status = "PASS with warnings"
        if status == "PASS" and fitting_info["requested"] and not fitting_info["applied"]:
            status = "PASS with warnings"
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
            errorbar_info,
            fitting_info,
            warnings,
            errors,
        )
        save_report(report)
        return 0 if status in {"PASS", "PASS with warnings"} else 1

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
            errorbar_info,
            fitting_info,
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
