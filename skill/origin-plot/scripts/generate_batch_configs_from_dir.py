from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCAN_REPORT_PATH = PROJECT_ROOT / "reports" / "origin_plot_v0_4_scan_report.json"
SUPPORTED_FORMATS = {"csv", "xlsx", "tsv", "txt"}
SUFFIX_TO_FORMAT = {
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".tsv": "tsv",
    ".txt": "txt",
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
        raise ValueError("Scan config must be a YAML mapping.")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    try:
        import yaml
    except ModuleNotFoundError:
        raise RuntimeError("Please install PyYAML: py -m pip install pyyaml") from None

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def read_dataframe(path: Path, detected_format: str):
    import pandas as pd

    if detected_format == "csv":
        return pd.read_csv(path)
    if detected_format == "xlsx":
        return pd.read_excel(path, engine="openpyxl")
    if detected_format == "tsv":
        return pd.read_csv(path, sep="\t")
    if detected_format == "txt":
        return pd.read_csv(path, sep=None, engine="python")
    raise ValueError(f"Unsupported input format: {detected_format}")


def scan_files(input_dir: Path, recursive: bool, allowed_formats: set[str]) -> list[tuple[Path, str]]:
    pattern = "**/*" if recursive else "*"
    found: list[tuple[Path, str]] = []
    for path in sorted(input_dir.glob(pattern)):
        if not path.is_file():
            continue
        detected_format = SUFFIX_TO_FORMAT.get(path.suffix.lower())
        if detected_format and detected_format in allowed_formats:
            found.append((path, detected_format))
    return found


def numeric_columns(df) -> list[str]:
    import pandas as pd

    usable: list[str] = []
    for column in df.columns:
        converted = pd.to_numeric(df[column], errors="coerce")
        if converted.notna().sum() >= 2:
            usable.append(str(column))
    return usable


def make_plot_config(scan_config: dict[str, Any], data_file: Path, detected_format: str, numeric: list[str]) -> dict[str, Any]:
    stem = data_file.stem
    x_column = numeric[0]
    y_columns = numeric[1:]
    output_root = str(scan_config["output_root"]).replace("\\", "/").rstrip("/")
    return {
        "input_file": rel(data_file),
        "input_format": detected_format,
        "sheet_name": None,
        "style_profile": scan_config.get("style_profile"),
        "export_profile": scan_config.get("export_profile"),
        "x_column": x_column,
        "y_columns": y_columns,
        "graph_type": str(scan_config.get("graph_type", "line")),
        "graph_title": str(scan_config.get("graph_title_template", "{stem}")).format(
            stem=stem,
            x_column=x_column,
        ),
        "x_title": str(scan_config.get("x_title_template", "{x_column}")).format(
            stem=stem,
            x_column=x_column,
        ),
        "y_title": str(scan_config.get("y_title", "Y")),
        "output_dir": f"{output_root}/{stem}",
        "output_basename": stem,
        "show_origin": bool(scan_config.get("show_origin", True)),
        "save_opju": bool(scan_config.get("save_opju", True)),
        "export_png": bool(scan_config.get("export_png", True)),
        "export_pdf": bool(scan_config.get("export_pdf", True)),
        "png_width": int(scan_config.get("png_width", 1400)),
    }


def report_status(generated_count: int, failed_count: int) -> str:
    if generated_count > 0 and failed_count == 0:
        return "PASS"
    if generated_count > 0 and failed_count > 0:
        return "PARTIAL PASS"
    return "FAIL"


def save_report(report: dict[str, Any]) -> None:
    SCAN_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCAN_REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate origin-plot batch configs by scanning a data directory.")
    parser.add_argument("--scan-config", default="configs/scan/scan_config.yaml")
    args = parser.parse_args()

    scan_config_path = resolve_project_path(args.scan_config)
    scan_name = scan_config_path.stem
    generated_configs: list[str] = []
    failures: list[dict[str, str]] = []
    files_seen = 0
    files_supported = 0
    generated_batch_config = None
    input_dir_report = None

    try:
        scan_config = load_yaml(scan_config_path)
        scan_name = str(scan_config["scan_name"])
        if scan_config.get("x_column_strategy") != "first_numeric":
            raise ValueError("x_column_strategy v0.4 supports only first_numeric.")
        if scan_config.get("y_column_strategy") != "remaining_numeric":
            raise ValueError("y_column_strategy v0.4 supports only remaining_numeric.")

        input_dir = resolve_project_path(str(scan_config["input_dir"]))
        input_dir_report = rel(input_dir)
        if not input_dir.exists():
            raise FileNotFoundError(f"input_dir does not exist: {rel(input_dir)}")

        allowed_formats = {str(fmt).lower() for fmt in scan_config.get("input_formats", [])}
        allowed_formats = allowed_formats & SUPPORTED_FORMATS
        if not allowed_formats:
            raise ValueError(f"input_formats must include at least one of {sorted(SUPPORTED_FORMATS)}.")

        files = scan_files(input_dir, bool(scan_config.get("recursive", False)), allowed_formats)
        files_seen = len(list(input_dir.rglob("*") if scan_config.get("recursive", False) else input_dir.glob("*")))
        files_supported = len(files)

        generated_dir = resolve_project_path(str(scan_config["generated_config_dir"]))
        jobs: list[dict[str, str]] = []
        seen_names: dict[str, int] = {}

        for data_file, detected_format in files:
            try:
                df = read_dataframe(data_file, detected_format)
                numeric = numeric_columns(df)
                if len(numeric) < 2:
                    raise ValueError("fewer than two numeric columns")
                base_name = data_file.stem
                seen_names[base_name] = seen_names.get(base_name, 0) + 1
                job_name = base_name if seen_names[base_name] == 1 else f"{base_name}_{seen_names[base_name]}"
                config_path = generated_dir / f"{job_name}_plot_config.yaml"
                plot_config = make_plot_config(scan_config, data_file, detected_format, numeric)
                write_yaml(config_path, plot_config)
                generated_configs.append(rel(config_path))
                jobs.append({"name": job_name, "config": rel(config_path)})
            except Exception as exc:  # noqa: BLE001 - record failure and continue scanning
                failures.append({"file": rel(data_file), "reason": f"{type(exc).__name__}: {exc}"})

        generated_batch_path = resolve_project_path(str(scan_config["generated_batch_config"]))
        generated_batch_config = rel(generated_batch_path)
        write_yaml(
            generated_batch_path,
            {
                "batch_name": scan_name,
                "continue_on_error": bool(scan_config.get("continue_on_error", True)),
                "jobs": jobs,
            },
        )

    except Exception as exc:  # noqa: BLE001 - scan must still write report
        failures.append({"file": rel(scan_config_path), "reason": f"{type(exc).__name__}: {exc}"})

    status = report_status(len(generated_configs), len(failures))
    report = {
        "status": status,
        "scan_name": scan_name,
        "input_dir": input_dir_report,
        "files_seen": files_seen,
        "files_supported": files_supported,
        "configs_generated": len(generated_configs),
        "failed_count": len(failures),
        "generated_batch_config": generated_batch_config,
        "generated_configs": generated_configs,
        "failures": failures,
    }
    save_report(report)

    print(f"scan_name: {scan_name}")
    print(f"files_seen: {files_seen}")
    print(f"files_supported: {files_supported}")
    print(f"configs_generated: {len(generated_configs)}")
    print(f"failed_count: {len(failures)}")
    print(f"generated_batch_config: {generated_batch_config}")
    print(f"report path: {rel(SCAN_REPORT_PATH)}")
    return 0 if status in {"PASS", "PARTIAL PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
