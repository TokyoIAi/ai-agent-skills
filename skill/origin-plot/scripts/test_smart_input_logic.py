"""Smoke tests for v0.9 smart input understanding helpers.

Run from ``skill/origin-plot/``:

    py scripts\\test_smart_input_logic.py

These tests do not call Origin. They exercise the pure-Python parsing,
column-role inference, graph-type recommendation, and config emission paths
in :mod:`analyze_data_source`.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parents[0]
sys.path.insert(0, str(SCRIPTS_DIR))

from analyze_data_source import (  # noqa: E402
    analyze,
    extract_first_markdown_table,
    find_error_columns,
    find_group_columns,
    markdown_to_dataframe,
    recommend_graph_type,
    select_roles,
    split_column_unit,
    detect_columns,
)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_extract_first_markdown_table() -> None:
    text = """# title

Some prose.

| x | y |
|---|---|
| 1 | 2 |
| 3 | 4 |

trailing notes
"""
    table = extract_first_markdown_table(text)
    assert_true(table is not None, "expected a table")
    headers, rows = table  # type: ignore[misc]
    assert_true(headers == ["x", "y"], f"headers mismatch: {headers!r}")
    assert_true(rows == [["1", "2"], ["3", "4"]], f"rows mismatch: {rows!r}")


def test_markdown_to_dataframe() -> None:
    sample_path = PROJECT_ROOT / "data" / "smart_inputs" / "sample_markdown_table.md"
    df = markdown_to_dataframe(sample_path)
    assert_true(len(df.columns) >= 2, f"expected >=2 columns, got {df.columns.tolist()}")
    assert_true(len(df) >= 2, f"expected >=2 rows, got {len(df)}")


def test_split_column_unit() -> None:
    cases = [
        ("\u8ddd\u79bb(cm)", ("\u8ddd\u79bb", "cm")),
        ("temperature [C]", ("temperature", "C")),
        ("plain", ("plain", None)),
    ]
    for col, expected in cases:
        assert_true(
            split_column_unit(col) == expected,
            f"split_column_unit({col!r}) returned {split_column_unit(col)!r}",
        )


def test_error_column_suffix_detection() -> None:
    rules = {
        "infer_error_columns_by_suffix": True,
        "error_column_suffixes": ["_err", "_error", "\u8bef\u5dee"],
    }
    numeric = ["x", "y", "y_err", "intensity", "intensity_error"]
    mapping = find_error_columns(numeric, rules)
    assert_true(mapping.get("y") == "y_err", f"y -> y_err mapping missing: {mapping!r}")
    assert_true(
        mapping.get("intensity") == "intensity_error",
        f"intensity -> intensity_error mapping missing: {mapping!r}",
    )


def test_group_column_detection() -> None:
    rules = {
        "infer_group_columns_by_text": True,
        "group_column_candidates": ["group", "type", "\u7c7b\u522b"],
    }
    matches = find_group_columns(["group", "comment"], rules)
    assert_true("group" in matches, f"group column missing: {matches!r}")


def test_units_extraction_via_detect_columns() -> None:
    import pandas as pd

    df = pd.DataFrame(
        {
            "\u8ddd\u79bb(cm)": [1.0, 2.0, 3.0],
            "\u529f\u7387(W)": [0.5, 1.2, 2.0],
        }
    )
    info = detect_columns(df, role_rules={})
    assert_true("\u8ddd\u79bb(cm)" in info["units"], f"missing unit for distance: {info['units']!r}")
    assert_true(info["units"]["\u8ddd\u79bb(cm)"] == "cm", f"unit mismatch: {info['units']!r}")


def test_recommend_graph_type_rules() -> None:
    column_info = {"numeric_columns": ["x", "y"], "text_columns": []}
    roles_simple = {
        "selected_roles": {
            "x_column": "x",
            "y_columns": ["y"],
            "y_error_columns": {},
            "group_column": None,
        }
    }
    assert_true(
        recommend_graph_type(roles_simple, column_info)[0] == "line",
        "simple x+y should recommend line",
    )

    roles_err = {
        "selected_roles": {
            "x_column": "x",
            "y_columns": ["y"],
            "y_error_columns": {"y": "y_err"},
            "group_column": None,
        }
    }
    assert_true(
        recommend_graph_type(roles_err, column_info)[0] == "errorbar",
        "errors should recommend errorbar",
    )

    roles_group = {
        "selected_roles": {
            "x_column": "time",
            "y_columns": ["value"],
            "y_error_columns": {},
            "group_column": "group",
        }
    }
    assert_true(
        recommend_graph_type(roles_group, column_info)[0] == "grouped_line",
        "group + value should recommend grouped_line",
    )


def test_smart_config_generation_for_csv() -> None:
    cfg = {
        "input_file": "data/smart_inputs/sample_excel_like.csv",
        "input_format": "auto",
        "smart_analysis": {"enabled": True},
        "role_inference_rules": {
            "x_column_candidates": ["distance", "\u8ddd\u79bb"],
        },
        "output": {
            "generated_config_path": "configs/generated/smart_test_generated.yaml",
            "smart_report_path": "reports/smart_test_analysis_report.json",
            "output_dir": "output/origin_plot_smart",
            "style_profile": "configs/styles/lab_report_style.yaml",
            "export_profile": "configs/exports/default_export.yaml",
        },
    }
    report = analyze(cfg)
    try:
        assert_true(
            report["status"] in {"PASS", "PARTIAL PASS"},
            f"smart config generation should not FAIL; status={report['status']!r}",
        )
        generated = PROJECT_ROOT / report["generated_plot_config"]
        assert_true(generated.exists(), f"generated plot config missing: {generated}")
        assert_true(report["selected_roles"]["x_column"], "x_column should be present")
        assert_true(report["selected_roles"]["y_columns"], "y_columns should be present")
    finally:
        # Cleanup the smoke-test artifacts so they do not pollute committed reports.
        for relative in (
            report["generated_plot_config"],
            cfg["output"]["smart_report_path"],
        ):
            target = PROJECT_ROOT / relative
            try:
                target.unlink()
            except FileNotFoundError:
                pass


def run_all() -> int:
    tests = [
        test_extract_first_markdown_table,
        test_markdown_to_dataframe,
        test_split_column_unit,
        test_error_column_suffix_detection,
        test_group_column_detection,
        test_units_extraction_via_detect_columns,
        test_recommend_graph_type_rules,
        test_smart_config_generation_for_csv,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"ok: {test.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL: {test.__name__}: {exc}")
        except Exception:  # noqa: BLE001
            failed += 1
            print(f"FAIL: {test.__name__} raised an unexpected error")
            traceback.print_exc()
    if failed:
        print(f"FAIL: {failed} test(s) failed")
        return 1
    print("PASS: smart input logic smoke tests ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_all())
