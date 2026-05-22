# contracts/

This directory is the **Codex / origin-plot boundary** in document form.
It tells Codex (or any equivalent caller) what `origin-plot` expects
upstream and what it refuses to do.

> **Codex writes canonical data and config. origin-plot executes.**

`origin-plot` does not infer column roles, does not auto-detect Excel
sheets or header rows, does not parse Markdown / images / OCR, and does
not guess the user's intent. Anything that requires those capabilities
must be done **before** `workflows/run_plot.py` is invoked.

## Documents

| File | Purpose |
|---|---|
| [`canonical_data_contract.md`](canonical_data_contract.md) | What canonical CSV / XLSX / TSV / TXT input looks like (formats, header convention, error and group columns, encoding, sorting). |
| [`plot_config_schema.md`](plot_config_schema.md) | Required and optional fields in the plot YAML; the v1.0 supported graph types; what was removed in v1.0. |
| [`codex_data_wrangler_contract.md`](codex_data_wrangler_contract.md) | The eight-step procedure Codex follows: read upstream, clean, standardise, persist, generate config, decide intent, invoke workflow, surface results. |
| [`non_goals.md`](non_goals.md) | Tier A (hard non-goals: never enter origin-plot) and tier B (possible future backend features under explicit canonical contracts). |

## Minimum canonical CSV

```csv
x,y
0,1.0
1,2.1
2,4.2
3,7.3
4,11.0
```

- UTF-8, no BOM.
- Header row present.
- Numeric columns coerce cleanly via `pandas.to_numeric`.
- Sort by `x` if monotonicity matters; `origin-plot` does not sort.

For uncertainty:

```csv
x,y,y_err
0,1.0,0.10
1,1.8,0.15
2,4.1,0.20
```

- The error suffix convention is `<y>_err` (or `_error`, `_uncertainty`,
  `误差`, `标准差`).
- Error columns must be non-negative.

## Minimum YAML plot config

```yaml
input_file: "data/cleaned/<dataset>.csv"
input_format: "auto"
sheet_name: null

x_column: "x"
y_columns:
  - "y"

graph_type: "line"
graph_title: "<title>"
x_title: "X"
y_title: "Y"

style_profile: "configs/styles/lab_report_style.yaml"
export_profile: "configs/exports/default_export.yaml"

output_dir: "output/<run-name>"
output_basename: "<basename>"

show_origin: true
```

For an errorbar plot, add:

```yaml
y_error_columns:
  y: "y_err"
graph_type: "errorbar"
```

For a fitting overlay, add the `fitting:` block exactly as shown in
[`configs/examples/fitting_plot.yaml`](../configs/examples/fitting_plot.yaml).
The full schema is in [`plot_config_schema.md`](plot_config_schema.md).

## Cross-links

- Daily entry surface: [`../workflows/README.md`](../workflows/README.md)
- Worked examples: [`../configs/examples/`](../configs/examples/)
- Sample canonical data: [`../data/examples/`](../data/examples/)
- Why v0.9 smart-input is not in scope:
  [`../archive/v0_9_smart_input_reference.md`](../archive/v0_9_smart_input_reference.md)
- Hard non-goals: [`non_goals.md`](non_goals.md)
