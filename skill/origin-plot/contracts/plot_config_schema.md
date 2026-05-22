# Plot config schema (v1.0 core)

`workflows/run_plot.py` consumes a YAML plot config that the legacy
validator (`scripts/validate_origin_plot_config.py`) recognises as well. The
core layer narrows the surface area to fields that the v0.8.7 stability
work verified end-to-end.

## Required fields

| Field | Type | Notes |
|---|---|---|
| `input_file` | string | Project-relative path to a canonical CSV / XLSX / TSV / TXT file. |
| `x_column` | string | Header of the X column. |
| `y_columns` | list of string | One or more Y columns. |
| `graph_type` | string | One of `line`, `scatter`, `line_symbol`, `errorbar`. |
| `output_dir` | string | Project-relative output directory. |
| `output_basename` | string | Filename stem for PNG / PDF / OPJU. |

## Optional fields

| Field | Type | Notes |
|---|---|---|
| `input_format` | string | `auto` (default) or one of `csv`/`xlsx`/`tsv`/`txt`/`xls`. |
| `sheet_name` | string \| int \| null | Excel sheet to read; ignored otherwise. |
| `y_error_columns` | mapping | `<y_column>: <error_column>`; non-negative numeric. |
| `x_error_column` | string | Optional X uncertainty column. |
| `graph_title` | string | Origin graph title. |
| `x_title`, `y_title` | string | Axis titles. |
| `style_profile` | string | Path to a `configs/styles/*.yaml` file. |
| `export_profile` | string | Path to a `configs/exports/*.yaml` file. |
| `save_opju`, `export_png`, `export_pdf` | bool | Output toggles (default true). |
| `png_width` | int | PNG export width override. |
| `show_origin` | bool | Toggle Origin window visibility. |
| `fitting` | mapping | Optional curve-fit configuration (linear / polynomial). |

## Removed in v1.0 core

- `grouped_line` / `grouped_scatter` graph types.
- Markdown / image / OCR detection knobs.
- Smart inference rules (`smart_analysis`, `role_inference_rules`).

These responsibilities now sit upstream with Codex (see
`codex_data_wrangler_contract.md`).

## Backward compatibility

Existing v0.8.7 configs that only use the fields listed above continue to
work without modification. The legacy validator is still the single source
of truth, so anything that passed under v0.8.7 still passes under v1.0.

## Curve fitting

The fitting block is preserved verbatim from v0.8.7:

```yaml
fitting:
  enabled: true
  models:
    - name: linear_fit_y
      y_column: y
      model: linear
      output_curve_points: 100
      show_equation: true
      show_r_squared: true
```

Polynomial fits accept `degree: 2` (or higher up to 5).

## Example

```yaml
input_file: "data/examples/line_sample.csv"
input_format: "auto"
sheet_name: null

x_column: "x"
y_columns:
  - "y"

graph_type: "line"
graph_title: "Example line plot"
x_title: "X"
y_title: "Y"

style_profile: "configs/styles/lab_report_style.yaml"
export_profile: "configs/exports/default_export.yaml"

output_dir: "output/origin_plot_examples"
output_basename: "line_example"

show_origin: true
```
