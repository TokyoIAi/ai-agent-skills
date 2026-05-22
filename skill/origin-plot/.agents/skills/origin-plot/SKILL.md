---
name: origin-plot
description: Use this skill when the task involves generating scientific plots with Origin or OriginPro from CSV/Excel data using Windows Python and the originpro package. Do not use GUI clicking, pyautogui, screenshot recognition, or mouse-coordinate automation.
---

# Origin Plot

## Purpose

Use Windows Python and OriginLab's `originpro` package to generate verified scientific plots in installed Windows Origin/OriginPro from CSV or Excel data. Prefer direct API automation through Origin Automation Server / COM rather than any GUI interaction.

## When to Use

Use this skill for Origin/OriginPro plotting, Origin project generation, batch scientific plots, publication figures, and reproducible CSV/Excel-to-Origin workflows. Use the bundled scripts as templates and adapt them to project data and chart requirements.

## Hard Rules

- Do not use pyautogui.
- Do not use screenshot recognition.
- Do not use mouse-coordinate automation.
- Do not blindly operate the Origin GUI.
- Prefer originpro API.
- Use Windows Python for controlling installed Windows Origin.
- Do not claim success unless output files are actually generated and verified.
- Do not modify Origin installation files, registry entries, or system settings during diagnostics.
- Do not auto-click Origin dialogs.

## Environment Requirements

- Windows with desktop Origin or OriginPro installed, preferably Origin 2021 or later.
- Windows Python, not WSL Python, for COM-based Origin automation.
- Python packages: `originpro`, `pandas`, and `openpyxl`.
- A readable CSV or Excel input file with at least two numeric columns.
- Write access to the project `output/` directory.

## Expected Project Structure

```text
.agents/skills/origin-plot/
  SKILL.md
  scripts/
    check_origin_env.py
    plot_origin_template.py
  references/
    originpro_usage_notes.md
  assets/
    sample.csv
data/
  sample.csv
output/
  origin_env_report.json
  origin_plot/
```

## Standard Workflow

1. Inspect `data/` for CSV or Excel input files.
2. Run `py .agents\skills\origin-plot\scripts\check_origin_env.py`.
3. Load CSV/Excel data with pandas.
4. Create an Origin worksheet.
5. Send the dataframe to the worksheet.
6. Use the first numeric column as X by default.
7. Use remaining numeric columns as Y by default.
8. Create a line or scatter plot with the `originpro` API.
9. Set title, axis labels, and legend.
10. Rescale the graph layer.
11. Export PNG and PDF.
12. Save the Origin project as OPJU.
13. Verify output files exist before reporting success.

## Data Assumptions

- Default input is `data/sample.csv`; if missing, use `.agents/skills/origin-plot/assets/sample.csv`.
- CSV data should include headers.
- Excel input should be read with pandas and `openpyxl`.
- Numeric columns are selected with pandas dtype inspection.
- At least two numeric columns are required: one X column and one or more Y columns.

## Plotting Defaults

- Plot type: line plot unless the user asks for scatter or another style.
- X axis: first numeric column.
- Y series: all remaining numeric columns.
- Title: derived from the input filename unless the user specifies one.
- Axis labels: use source column names.
- Legend: use Y column names.
- Output directory: `output/origin_plot/`.

## Validation Commands

```powershell
py .agents\skills\origin-plot\scripts\check_origin_env.py
py .agents\skills\origin-plot\scripts\plot_origin_template.py
```

If `py` is unavailable, try the same commands with the Windows `python` executable. Do not use WSL Python to control Windows Origin.

## Acceptance Criteria

- Environment report generated.
- Script runs or reports missing prerequisite truthfully.
- Output PNG exists when Origin environment is available.
- Output PDF exists when Origin environment is available.
- Output OPJU exists when Origin environment is available.
- No GUI clicking automation used.

## Failure Handling

- If `originpro` is missing, report the import failure and suggest `py -m pip install originpro pandas openpyxl`.
- If `pandas` or `openpyxl` is missing, report the missing package before plotting.
- If running under WSL/Linux, explain that WSL Python usually cannot directly call Windows COM / Origin Automation.
- If Origin is not installed or COM launch fails, report that Origin automation is unavailable and do not claim plot generation.
- If Origin shows first-run/license/update dialogs, ask the user to complete initialization manually.
- If manual OK is required only once, document it as first-run manual initialization.
- If manual OK is required on every run, mark validation as PARTIAL PASS.
- If the data has fewer than two numeric columns, stop with a clear message.
- If expected output files are missing, list them and exit nonzero.

## Notes for Codex

- Read `references/originpro_usage_notes.md` when diagnosing failures or adapting the template to a new workflow.
- Start from `scripts/check_origin_env.py` before attempting plotting.
- Adapt `scripts/plot_origin_template.py` to the user's real input, labels, graph template, and export formats.
- Prefer deterministic file existence checks over visual inspection.
- Keep diagnostics read-only except for writing reports under `output/`.

## v0.2 Config-based Plotting

Use v0.2 when the user wants real project data plotted from a YAML configuration rather than editing the sample template. Run these commands from `skill/origin-plot/`:

```powershell
py scripts\validate_origin_plot_config.py --config configs\origin_plot_config.yaml
py scripts\origin_plot_from_config.py --config configs\origin_plot_config.yaml
```

The v0.2 scripts live at the subproject root under `scripts/` and keep the v0.1 `.agents\skills\origin-plot\scripts\plot_origin_template.py` baseline intact.

## Supported Input Formats

Current v0.2 supports:

- CSV
- XLSX
- TSV
- TXT delimited text

Current v0.2 does not formally support:

- XLS old Excel unless `xlrd` is installed.
- OPJU as input.
- Image data.
- Complex multi-layer Origin templates.

## YAML Configuration Schema

Use `configs/origin_plot_config.yaml` as the starting point. Required fields are `input_file`, `x_column`, `y_columns`, `graph_type`, `output_dir`, and `output_basename`.

- `input_format`: `auto`, `csv`, `xlsx`, `tsv`, `txt`, or `xls`.
- `graph_type`: `line`, `scatter`, or `line_symbol`.
- `show_origin`: show or hide Origin while automating.
- `save_opju`, `export_png`, `export_pdf`: control requested outputs.
- `png_width`: pixel width passed to Origin graph export for PNG.

## Validation Workflow

Run the validator before calling Origin. It loads YAML, resolves input format, reads data with pandas, checks required columns, confirms selected X/Y columns can become numeric, and verifies at least two valid data rows.

## Real Data Workflow

1. Copy or edit `configs/origin_plot_config.yaml`.
2. Point `input_file` to a CSV/XLSX/TSV/TXT file under the subproject.
3. Set `x_column`, `y_columns`, titles, output directory, and basename.
4. Run the validator.
5. Run `origin_plot_from_config.py`.
6. Verify requested PNG/PDF/OPJU outputs and `reports/origin_plot_v0_2_report.json`.

## Output Contract

The plotting script writes requested files under `output_dir` and writes `reports/origin_plot_v0_2_report.json` with relative paths, row counts, selected columns, warnings, errors, and output existence/size checks. `output/` is generated output and should not be committed.

## Failure Handling

If validation fails, do not call Origin. If Origin automation fails, print the full traceback, write a FAIL report, and do not claim success. If only some requested outputs exist, report `PARTIAL PASS`, list the missing files, and exit nonzero.

## Version Notes

- v0.1: sample CSV template plot using `.agents\skills\origin-plot\scripts\plot_origin_template.py`.
- v0.2: YAML-configured plotting for CSV/XLSX/TSV/TXT input using `scripts\validate_origin_plot_config.py` and `scripts\origin_plot_from_config.py`.
- v0.2.1: documents a first-run manual Origin dialog caveat; subsequent PowerShell rerun completed without popup.
- v0.3: batch plotting MVP using `scripts\origin_batch_plot.py` with a batch YAML listing multiple single-plot configs.
- v0.4: directory scan MVP using `scripts\generate_batch_configs_from_dir.py` to create single-plot configs and a generated batch config from data files.
- v0.5: style and export profile MVP using reusable YAML profiles under `configs\styles\` and `configs\exports\`.
- v0.6: error bar MVP using `graph_type: errorbar`, `y_error_columns`, and optional `x_error_column`.
- v0.7: curve fitting MVP using Python-side linear and polynomial fitting, with fit curves added to Origin as generated worksheet columns.
- v0.8: fit annotation, fitting summary CSV, and residual CSV plus optional residual plot artifacts on top of v0.7.
- v0.8.1: Origin COM session stability with retry-on-com-error, fit summary CSV append policy, fitting batch sample, and cross-report artifact summarizer.

## v0.3 Batch Plotting Workflow

Use v0.3 when the user wants to run several configured Origin plots in one command. Run from `skill/origin-plot/`:

```powershell
py scripts\origin_batch_plot.py --batch-config configs\batch\batch_plot_config.yaml
```

The batch script validates each single-plot config, runs `origin_plot_from_config.py`, records each job result, and writes `reports\origin_plot_v0_3_batch_report.json`. It uses the existing single-plot workflow so v0.1/v0.2 behavior stays intact.

## Batch YAML Schema

Required batch fields:

- `batch_name`: name for the batch report.
- `continue_on_error`: true to continue after a failed job, false to stop after first failure.
- `jobs`: non-empty list.
- `jobs[].name`: report-friendly job name.
- `jobs[].config`: path to a v0.2 single-plot YAML config.

## Batch Acceptance Criteria

- At least three jobs are listed for the sample MVP.
- Every job has a valid config path.
- Each requested job output is checked by real file existence and size.
- The batch report uses relative paths.
- Batch status is `PASS` only when every job passes.
- Scatter or line-symbol fallback is acceptable only when warnings are recorded.

## Failure Handling for Batch Jobs

Do not let one failed job prevent report creation. If `continue_on_error` is true, record the failed job and continue. If it is false, stop after the failed job but still write the batch report. Never use GUI automation to clear Origin dialogs; ask the user to complete first-run or license initialization manually.

## v0.4 Directory Scan Workflow

Use v0.4 when the user has many CSV/XLSX/TSV/TXT files and wants Codex to infer basic plotting configs automatically. Run from `skill/origin-plot/`:

```powershell
py scripts\generate_batch_configs_from_dir.py --scan-config configs\scan\scan_config.yaml
py scripts\origin_batch_plot.py --batch-config configs\generated\generated_batch_config.yaml
```

The scan step never calls Origin. It only reads data with pandas, infers columns, writes generated YAML configs, writes a generated batch config, and records `reports\origin_plot_v0_4_scan_report.json`.

## Scan YAML Schema

Required scan fields:

- `scan_name`: batch/report name.
- `input_dir`: directory containing data files.
- `recursive`: whether to scan nested directories.
- `input_formats`: supported values are `csv`, `xlsx`, `tsv`, and `txt`.
- `x_column_strategy`: v0.4 supports only `first_numeric`.
- `y_column_strategy`: v0.4 supports only `remaining_numeric`.
- `graph_type`: default graph type for generated plot configs.
- `output_root`: output root for generated plot outputs.
- `generated_config_dir`: destination for generated single-plot YAML configs.
- `generated_batch_config`: destination for generated batch YAML.
- `continue_on_error`: copied to the generated batch YAML.

## Auto Config Generation Rules

For each supported file, read it with pandas, find numeric or numeric-convertible columns, use the first numeric column as X, and use remaining numeric columns as Y. If a file cannot be read or has fewer than two numeric columns, record a failure and keep scanning other files.

## Retry Failed Jobs Workflow

When `origin_batch_plot.py` runs a batch with failed jobs, it writes `configs\generated\retry_failed_jobs.yaml` containing only failed jobs and records `retry_config` in `reports\origin_plot_v0_3_batch_report.json`. If no jobs fail, `retry_config.generated` is false and `failed_job_count` is 0.

## v0.4 Acceptance Criteria

- Directory scan generates at least one single-plot config.
- The sample scan generates at least three configs.
- `configs\generated\generated_batch_config.yaml` exists and uses relative paths.
- `reports\origin_plot_v0_4_scan_report.json` exists and uses relative paths.
- Generated batch plotting produces requested PNG/PDF/OPJU outputs.
- Batch report records retry config status.

## v0.5 Style Profile Workflow

Use v0.5 when users want consistent visual settings across single plots, generated directory-scan configs, and batch jobs. Add a reusable style profile reference to a plot config or scan config:

```yaml
style_profile: "configs/styles/lab_report_style.yaml"
```

Style profiles can define title/legend/rescale toggles, axis title toggles, light line settings, symbol size, and default export settings. Do not promise complex Origin template behavior; v0.5 does not use `.otpu` template reuse.

## Export Profile Workflow

Add an export profile reference to a plot config or scan config:

```yaml
export_profile: "configs/exports/default_export.yaml"
```

Export profiles define `export_png`, `export_pdf`, `save_opju`, and `png_width`. They are reusable across lab report, paper, and presentation workflows.

## Effective Config Merge Order

Effective export settings are merged from low to high priority:

1. `style_profile.export`
2. `export_profile`
3. explicit plot config fields

This preserves backward compatibility with v0.2 configs because existing explicit `export_png`, `export_pdf`, `save_opju`, and `png_width` fields still win.

## Style Warning Policy

Apply only lightweight Origin styling through `originpro`. If title, legend, rescale, axis title, line width, or symbol size operations fail, record the issue in `style.style_warnings` and continue. If requested PNG/PDF/OPJU files are generated and verified, the plot can still PASS with warnings. Never use GUI clicking or screenshot automation to apply style.

## v0.5 Acceptance Criteria

- Style profiles and export profiles load from relative paths.
- Validator reports style profile, export profile, and effective export settings.
- Single-plot report includes a `style` object.
- Batch report includes `style_summary`.
- Generated scan configs include style and export profile references.
- Requested PNG/PDF/OPJU outputs still exist.

## v0.6 Error Bar Workflow

Use v0.6 when the user provides uncertainty/error columns for one or more Y series. Validate first, then plot:

```powershell
py scripts\validate_origin_plot_config.py --config configs\errorbar\errorbar_single_config.yaml
py scripts\origin_plot_from_config.py --config configs\errorbar\errorbar_single_config.yaml
```

For multi-series error bars, map each Y column to its own error column.

## Error Bar YAML Schema

```yaml
graph_type: "errorbar"
y_columns:
  - "y1"
  - "y2"
y_error_columns:
  y1: "y1_err"
  y2: "y2_err"
x_error_column: null
```

`y_error_columns` is a mapping whose keys must be listed in `y_columns`. `x_error_column` is optional.

## Error Bar Validation Rules

- `graph_type` may be `errorbar`.
- Every `y_error_columns` key must belong to `y_columns`.
- Every referenced error column must exist.
- Error columns must be numeric or numeric-convertible.
- Error values must be non-negative.
- If `graph_type: errorbar` has no `y_error_columns`, allow ordinary plot fallback but record a warning.

## Error Bar Report Contract

Single-plot reports include:

```json
"errorbar": {
  "requested": true,
  "applied": true,
  "x_error_column": null,
  "y_error_columns": {},
  "warnings": []
}
```

Batch reports include `errorbar_summary` with counts for requesting jobs, applied jobs, and jobs with warnings.

## v0.6 Acceptance Criteria

- Error bar configs validate without calling Origin.
- Single-series and multi-series error bar configs generate requested PNG/PDF/OPJU files.
- `errorbar.applied` is true when Origin accepts the error-bar columns.
- If Origin rejects error bars but exports ordinary plot files, mark `PASS with warnings`.
- Reports use relative paths and do not claim GUI automation.

## v0.7 Curve Fitting Workflow

Use v0.7 when the user wants basic fit curves and fit metrics. Validate first, then plot:

```powershell
py scripts\validate_origin_plot_config.py --config configs\fitting\linear_fit_config.yaml
py scripts\origin_plot_from_config.py --config configs\fitting\linear_fit_config.yaml
```

Fitting is computed in Python with `numpy.polyfit`. Origin receives the original data and generated fit curve columns, then renders and exports the graph. Do not require Origin's built-in fitting API in v0.7.

## Fitting YAML Schema

```yaml
fitting:
  enabled: true
  models:
    - name: "linear_fit_y"
      y_column: "y"
      model: "linear"
      degree: 2
      output_curve_points: 100
      show_equation: true
      show_r_squared: true
```

`degree` is required for polynomial models and ignored for linear models.

## Supported Fit Models

- `linear`: uses `numpy.polyfit(x, y, 1)`.
- `polynomial`: uses `numpy.polyfit(x, y, degree)` with degree 2 through 5.

Unsupported models must produce warnings or validation failures; never claim unsupported fitting succeeded.

## Fitting Report Contract

Single-plot reports include:

```json
"fitting": {
  "requested": true,
  "applied": true,
  "models": [
    {
      "name": "...",
      "coefficients": [],
      "equation": "...",
      "r_squared": 0.0,
      "residual_sum_of_squares": 0.0,
      "curve_added_to_origin": true
    }
  ],
  "warnings": []
}
```

Batch reports include `fitting_summary` with counts for requesting jobs, applied jobs, jobs with warnings, and models used.

## v0.7 Acceptance Criteria

- Linear and polynomial fitting configs validate without calling Origin.
- Fit coefficients, equation, R squared, residual sum of squares, and point count are reported.
- Fit curve columns are added to the Origin worksheet.
- Fit curves are overlaid on the Origin graph when supported.
- Requested PNG/PDF/OPJU outputs exist.
- If fit curve overlay fails but exports exist, mark `PASS with warnings` and report the failure.

## v0.8 Fit Annotation Workflow

Use v0.8 fit annotations when the user wants the fitted equation, R squared, or model name displayed inside the Origin graph. Add an `annotation` block under `fitting`:

```yaml
fitting:
  annotation:
    enabled: true
    include_equation: true
    include_r_squared: true
    include_model_name: true
    position: "top_right"
```

`position` accepts `top_right`, `top_left`, `bottom_right`, or `bottom_left`. Annotation is best-effort through `layer.add_label`. Never claim annotation success if Origin rejects the call. Reports must always carry `fitting_annotation.applied` truthfully.

## Fit Summary CSV Contract

Use `fitting.summary_csv` to centralize fit metrics across runs. The CSV is appended across runs so a batch can build one summary file:

```yaml
fitting:
  summary_csv:
    enabled: true
    path: "reports/fitting_summary.csv"
```

`path` must be relative. Required columns:

- `config`
- `input_file`
- `fit_name`
- `y_column`
- `model`
- `degree`
- `coefficients` (semicolon separated string)
- `equation`
- `r_squared`
- `residual_sum_of_squares`
- `n_points`
- `curve_added_to_origin`
- `annotation_applied`

The single-plot report includes:

```json
"fitting_summary_csv": {
  "requested": true,
  "path": "reports/fitting_summary.csv",
  "exists": true,
  "rows_written": 1,
  "warnings": []
}
```

## Residual Data Workflow

Enable residual export when the user wants per-point residuals saved to disk:

```yaml
fitting:
  residuals:
    export_csv: true
    generate_residual_plot: true
    output_dir: "output/origin_plot_residuals"
```

`output_dir` must be relative. Residual CSVs are written under `reports/residuals/`:

```text
reports/residuals/<output_basename>_<fit_name>_residuals.csv
```

Required columns: `x`, `y_observed`, `y_fitted`, `residual`.

## Residual Plot Workflow

Residual plots use matplotlib (Agg backend) and write PNG plus PDF to the configured `output_dir`:

```text
output/origin_plot_residuals/<output_basename>_<fit_name>_residual.png
output/origin_plot_residuals/<output_basename>_<fit_name>_residual.pdf
```

If matplotlib is unavailable or the plot generation fails, record the issue under `residuals.warnings` and let the run finish as `PASS with warnings` provided main PNG/PDF/OPJU outputs exist.

The single-plot report includes:

```json
"residuals": {
  "csv_requested": true,
  "csv_outputs": [],
  "residual_plot_requested": true,
  "residual_plot_outputs": [],
  "warnings": []
}
```

## v0.8 Acceptance Criteria

- Fitting configs may include `annotation`, `summary_csv`, and `residuals` blocks. Configs without any of them remain valid.
- Validator rejects absolute paths in `fitting.summary_csv.path` and `fitting.residuals.output_dir`.
- Validator rejects unsupported `fitting.annotation.position` values.
- Reports always include `fitting_annotation`, `fitting_summary_csv`, and `residuals` fields, even when not requested.
- Annotation success or failure is reported truthfully through `fitting_annotation.applied`.
- `fitting_summary.csv` exists with the requested rows and columns when `summary_csv.enabled=true`.
- Residual CSVs exist and have the four required columns when `residuals.export_csv=true`.
- Residual PNG and PDF exist when `residuals.generate_residual_plot=true` and matplotlib is available.
- Batch report includes a `fit_artifact_summary` block with annotation counts, summary CSV outputs, residual CSV count, residual plot count, and jobs with fit-artifact warnings.
- Reports use relative paths and never claim GUI automation.

## Origin Session Retry Policy (v0.8.1)

The Origin block in `origin_plot_from_config.py` is wrapped in a retry loop driven by `origin_session`:

```yaml
origin_session:
  retry_on_com_error: true
  max_retries: 1
  kill_stale_origin_before_retry: true
  retry_delay_seconds: 2
```

Retry triggers only when an exception text matches known Origin/COM markers (for example `OriginExt`, `originpro`, `ApplicationBase_LT_execute`, `set_show`, `\u65e0\u6548\u6307\u9488`). Non-Origin failures fail fast.

Before each retry the script:

- Calls `op.exit()` to release the previous Origin handle.
- Optionally runs `taskkill /F /IM Origin64.exe` (and `Origin.exe`, `OriginPro.exe`) when `kill_stale_origin_before_retry=true` and the platform is Windows.
- Sleeps `retry_delay_seconds`.
- Resets per-attempt state (warnings, fit/annotation applied flags, annotation texts).

Records every classified failure in `origin_session.session_errors`. Final status is exposed via `origin_session.final_session_status` (`ok`, `ok_after_retry`, `failed`, or `not_started`).

If retry succeeds, the run status moves to `PASS with session_retry`, which the batch script and artifact summarizer treat as passing. Never claim retry succeeded if `final_session_status` is not `ok` or `ok_after_retry`.

## Fitting Summary CSV Append Policy (v0.8.1)

`fitting.summary_csv.append` defaults to `true` to preserve v0.8 behavior. When `append=false`, the script truncates the configured CSV before writing the current run, removing stale rows from prior runs of the same config. Combine `append=false` with distinct paths per config (for example `reports/fitting_summary_linear.csv` and `reports/fitting_summary_poly2.csv`) to avoid mutual overwrites.

The single-plot report now includes `fitting_summary_csv.append`.

## Fit Artifact Summary Workflow (v0.8.1)

`scripts/summarize_fit_artifacts.py` aggregates fit artifacts across single-plot and batch reports. Inputs come from explicit paths (`--reports A.json B.json`) or a directory (`--reports-dir reports`). Output defaults to `reports/origin_plot_v0_8_artifact_report.json` and is always a relative path.

The summary report carries:

- `reports_scanned`, `reports_unreadable`, `scanned_paths`.
- `fit_models_seen`, `annotations_requested`, `annotations_applied`.
- Deduplicated `summary_csv_outputs`, `residual_csv_outputs`, and `residual_plot_outputs` with `exists` flags.
- `missing_artifacts` listing recorded paths that are no longer on disk.
- `warnings` collected from each entry's annotation, summary CSV, and residuals warnings.
- `status`: `PASS`, `PASS with warnings` when any artifact is missing, or `FAIL` when nothing was scanned.

The aggregator only inspects paths the source reports recorded. It does not glob `output/` and does not call Origin.

## v0.8.1 Acceptance Criteria

- Validator accepts and reports `origin_session` settings with sane defaults.
- Validator accepts `fitting.summary_csv.append` as a boolean.
- Single-plot report carries `origin_session` with `attempts`, `retry_used`, `stale_origin_killed`, `session_errors`, and `final_session_status`.
- `PASS with session_retry` is honored by the single-plot exit code, batch script, and summarizer.
- `configs/batch/fitting_batch_config.yaml` exercises both fit configs and produces non-zero `fit_artifact_summary` counters.
- Batch report includes `origin_session_summary` alongside `fit_artifact_summary`.
- `scripts/summarize_fit_artifacts.py` writes `reports/origin_plot_v0_8_artifact_report.json` with relative paths and existence checks.
- All reports remain free of absolute paths (`H:\\`, `C:\\`, `E:\\`).
- `output/` stays git-ignored; `reports/*.csv`, `reports/residuals/*.csv`, and `reports/origin_plot_v0_8_artifact_report.json` are committable.
