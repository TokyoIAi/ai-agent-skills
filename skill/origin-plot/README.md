# origin-plot

`origin-plot` is a Codex Agent Skill for reproducible scientific plotting with Windows Python, `originpro`, and local Origin / OriginPro. It uses API automation, not GUI clicking, screenshot recognition, or mouse-coordinate automation.

Current version: v0.8.4.

## Supported formats

- CSV
- XLSX
- TSV
- TXT delimited text

Not formally supported in v0.2: old XLS unless `xlrd` is installed, OPJU as input, image data, and complex multi-layer Origin templates.

## Dependencies

Install into the Windows Python environment used by Codex:

```powershell
py -m pip install -r requirements.txt
```

## Environment detection

Run from `skill/origin-plot/`:

```powershell
py .agents\skills\origin-plot\scripts\check_origin_env.py
```

The report is written to `output/origin_env_report.json`.

## v0.1 sample plotting

```powershell
py .agents\skills\origin-plot\scripts\plot_origin_template.py
```

This reads `data/sample.csv` and writes sample PNG/PDF/OPJU files under `output/origin_plot/`.

## v0.2 config-based plotting

Validate the YAML first:

```powershell
py scripts\validate_origin_plot_config.py --config configs\origin_plot_config.yaml
```

Generate the plot:

```powershell
py scripts\origin_plot_from_config.py --config configs\origin_plot_config.yaml
```

## v0.3 Batch Plotting

Batch plotting reads a batch YAML file that lists multiple single-plot YAML configs.

Default batch config:

```text
configs/batch/batch_plot_config.yaml
```

Run from `skill/origin-plot/`:

```powershell
py scripts\origin_batch_plot.py --batch-config configs\batch\batch_plot_config.yaml
```

Batch YAML fields:

- `batch_name`: name written to the batch report.
- `continue_on_error`: when true, a failed job is recorded and later jobs still run.
- `jobs`: non-empty list of jobs.
- `jobs[].name`: job name in the report.
- `jobs[].config`: path to a single-plot config YAML.

The batch report is written to:

```text
reports/origin_plot_v0_3_batch_report.json
```

Single job failures do not cause the batch script to exit without a report. The batch status is `PASS` when all jobs pass, `PARTIAL PASS` when some pass and some fail, and `FAIL` when all jobs fail.

## v0.4 Directory Scan and Auto Batch Config

Place multiple CSV/XLSX/TSV/TXT files under:

```text
data/batch_inputs/
```

Generate single-plot configs and a batch config:

```powershell
py scripts\generate_batch_configs_from_dir.py --scan-config configs\scan\scan_config.yaml
```

The scan step does not call Origin. It only reads data files, infers numeric X/Y columns, writes generated YAML configs, and writes `reports/origin_plot_v0_4_scan_report.json`.

Scan YAML fields:

- `scan_name`: name for generated batch and report.
- `input_dir`: directory to scan.
- `recursive`: scan nested directories when true.
- `input_formats`: allowed formats: `csv`, `xlsx`, `tsv`, `txt`.
- `x_column_strategy`: v0.4 supports `first_numeric`.
- `y_column_strategy`: v0.4 supports `remaining_numeric`.
- `graph_type`: default graph type for generated configs.
- `output_root`: output root used by generated plot configs.
- `generated_config_dir`: destination for generated single-plot YAML files.
- `generated_batch_config`: generated batch YAML path.
- `continue_on_error`: copied to the generated batch config.

Run the generated batch:

```powershell
py scripts\origin_batch_plot.py --batch-config configs\generated\generated_batch_config.yaml
```

The batch script performs the real Origin plotting. If any job fails, it writes `configs/generated/retry_failed_jobs.yaml` containing only failed jobs and records `retry_config` in `reports/origin_plot_v0_3_batch_report.json`.

## v0.5 Style Profiles and Export Profiles

Style profiles are reusable YAML files under `configs/styles/` that describe light graph behavior such as title, legend, rescale, axis title toggles, line width, symbol size, and default export settings. Export profiles are reusable YAML files under `configs/exports/` that focus only on export switches and PNG width.

Example single-plot config references:

```yaml
style_profile: "configs/styles/lab_report_style.yaml"
export_profile: "configs/exports/default_export.yaml"
```

Scan configs can also reference the same fields. Generated plot configs copy those references so a directory scan can produce a consistently styled batch.

Effective export settings merge in this order, lowest to highest priority:

1. `style_profile.export`
2. `export_profile`
3. explicit fields in the plot config

The style layer is best-effort. Stable settings such as title, axis titles, legend refresh, rescale, line width, and symbol size are attempted through `originpro`. If an Origin API or plot type does not accept a style operation, the script records a `style_warnings` entry and still treats the job as PASS when requested PNG/PDF/OPJU outputs exist.

This skill still does not use GUI automation, screenshot recognition, mouse-coordinate clicking, or auto-clicking of Origin dialogs.

## v0.6 Error Bar MVP

Error bar plots use `graph_type: errorbar` and map each Y series to its error column:

```yaml
y_columns:
  - "y1"
  - "y2"

y_error_columns:
  y1: "y1_err"
  y2: "y2_err"

x_error_column: null
graph_type: "errorbar"
```

Single-series example:

```powershell
py scripts\validate_origin_plot_config.py --config configs\errorbar\errorbar_single_config.yaml
py scripts\origin_plot_from_config.py --config configs\errorbar\errorbar_single_config.yaml
```

Multi-series example:

```powershell
py scripts\validate_origin_plot_config.py --config configs\errorbar\errorbar_multi_config.yaml
py scripts\origin_plot_from_config.py --config configs\errorbar\errorbar_multi_config.yaml
```

`x_error_column` is optional. When present, it must name a numeric, non-negative column.

Error bar application is best-effort through `originpro`. If Origin rejects the error-bar call, the script records `errorbar.warnings`, falls back to ordinary plotting when possible, and still exports PNG/PDF/OPJU. In that case the result is `PASS with warnings`, not a false claim that error bars were applied.

## v0.7 Curve Fitting MVP

Curve fitting is performed in Python, then the generated fit curve data is sent to Origin as extra worksheet columns. Origin handles graph rendering, PNG/PDF export, and OPJU saving. v0.7 does not depend on Origin's built-in fitting API.

YAML schema:

```yaml
fitting:
  enabled: true
  models:
    - name: "linear_fit_y"
      y_column: "y"
      model: "linear"
      output_curve_points: 100
      show_equation: true
      show_r_squared: true
```

Polynomial fitting adds a degree:

```yaml
fitting:
  enabled: true
  models:
    - name: "poly2_fit_y"
      y_column: "y"
      model: "polynomial"
      degree: 2
      output_curve_points: 100
```

Run examples:

```powershell
py scripts\validate_origin_plot_config.py --config configs\fitting\linear_fit_config.yaml
py scripts\origin_plot_from_config.py --config configs\fitting\linear_fit_config.yaml

py scripts\validate_origin_plot_config.py --config configs\fitting\poly2_fit_config.yaml
py scripts\origin_plot_from_config.py --config configs\fitting\poly2_fit_config.yaml
```

Reports include coefficients, an equation string, R squared, residual sum of squares, point count, and whether the fit curve was added to the Origin graph. If PNG/PDF/OPJU export succeeds but a fit curve cannot be added, the result is `PASS with warnings`.

## v0.8 Fit Annotation, Summary CSV, and Residuals

v0.8 extends v0.7 with three optional artifacts: in-graph fit annotations, a fit summary CSV that aggregates each fit model, and residual data export with an optional residual plot.

### `fitting.annotation` schema

```yaml
fitting:
  annotation:
    enabled: true
    include_equation: true
    include_r_squared: true
    include_model_name: true
    position: "top_right"
```

`position` accepts `top_right`, `top_left`, `bottom_right`, or `bottom_left`. Annotation is best-effort through `originpro`. If Origin rejects the call or the layer axis range is unavailable, the script records `fitting_annotation.warnings`, leaves `fitting_annotation.applied=false`, and still exports PNG/PDF/OPJU.

### `fitting.summary_csv` schema

```yaml
fitting:
  summary_csv:
    enabled: true
    path: "reports/fitting_summary.csv"
```

`path` must be relative; absolute paths fail validation. The CSV is appended across runs so multiple plots can share one summary file.

`fitting_summary.csv` columns:

- `config`
- `input_file`
- `fit_name`
- `y_column`
- `model`
- `degree`
- `coefficients` (semicolon separated)
- `equation`
- `r_squared`
- `residual_sum_of_squares`
- `n_points`
- `curve_added_to_origin`
- `annotation_applied`

### `fitting.residuals` schema

```yaml
fitting:
  residuals:
    export_csv: true
    generate_residual_plot: true
    output_dir: "output/origin_plot_residuals"
```

`output_dir` must be relative; absolute paths fail validation.

Residual CSVs are written under `reports/residuals/`, one file per fit:

```text
reports/residuals/<output_basename>_<fit_name>_residuals.csv
```

Residual CSV columns:

- `x`
- `y_observed`
- `y_fitted`
- `residual`

Residual plots use matplotlib and write PNG/PDF under the configured `output_dir`:

```text
output/origin_plot_residuals/<output_basename>_<fit_name>_residual.png
output/origin_plot_residuals/<output_basename>_<fit_name>_residual.pdf
```

### Status policy

The single-plot status moves from `PASS` to `PASS with warnings` when any of the following are true:

- Annotation was requested but `fitting_annotation.applied=false`.
- Summary CSV was requested but the file does not exist after the run.
- Any residual warning was recorded.

Annotation, summary CSV, and residual plot generation are best-effort artifacts. If main PNG/PDF/OPJU exports succeed and any single artifact fails, the run is reported as `PASS with warnings`. The script never claims an artifact was applied when it was not.

### Backward compatibility

Configurations without `fitting.annotation`, `fitting.summary_csv`, or `fitting.residuals` continue to work. Reports always emit the three v0.8 fields (`fitting_annotation`, `fitting_summary_csv`, `residuals`) with `requested=false` defaults.

## v0.8.1 Origin Session Stability and Fit Artifact Hygiene

v0.8.1 hardens Origin COM session handling, makes the fitting summary CSV idempotent, and adds a cross-report artifact summary tool. No new plot styles, fit models, or layout work is included.

### Why retries are needed

The Origin COM bridge through `originpro` / `OriginExt` can occasionally raise transient errors after several chained sessions, for example:

- `RuntimeError: Exception in OriginExt::ApplicationBase::LT_execute ==> 无效指针`
- `SystemError: <built-in function ApplicationBase_LT_execute> returned a result with an exception set`

Stopping any stale `Origin64.exe` and starting a fresh session typically clears the issue. v0.8.1 captures these failures and can retry once with a clean handle instead of failing.

### `origin_session` schema

```yaml
origin_session:
  retry_on_com_error: true
  max_retries: 1
  kill_stale_origin_before_retry: true
  retry_delay_seconds: 2
```

Defaults match the example. `max_retries` is capped between 0 and 5; `retry_delay_seconds` is capped between 0 and 60. The retry strategy is:

1. Wrap the Origin block (`set_show`, worksheet creation, plotting, exports, OPJU save) in an attempt loop.
2. On failure, classify the exception. Only known Origin/COM markers trigger a retry; non-Origin errors fail fast.
3. Before retry, call `op.exit()`, optionally run `taskkill /F /IM Origin64.exe` (and `Origin.exe`, `OriginPro.exe`), then sleep `retry_delay_seconds`.
4. Reset per-attempt state (warnings, applied flags, annotation texts) so the report only reflects the successful attempt.
5. After a successful retry, the run is reported as `PASS with session_retry`. If retries are exhausted the run is `FAIL` with the exception preserved.

The single-plot report adds:

```json
"origin_session": {
  "retry_on_com_error": true,
  "max_retries": 1,
  "kill_stale_origin_before_retry": true,
  "retry_delay_seconds": 2.0,
  "attempts": 1,
  "retry_used": false,
  "stale_origin_killed": false,
  "session_errors": [],
  "final_session_status": "ok"
}
```

`final_session_status` is one of `ok`, `ok_after_retry`, `failed`, or `not_started` (when the Origin block was never reached).

Process termination is conservative: only `Origin64.exe`, `Origin.exe`, and `OriginPro.exe` are signaled, and only as part of the retry path. The script never auto-clicks Origin GUI dialogs.

### Fit summary CSV append policy

`fitting.summary_csv` now accepts `append`:

```yaml
fitting:
  summary_csv:
    enabled: true
    path: "reports/fitting_summary_linear.csv"
    append: false
```

`append: true` (default) preserves existing rows across runs. `append: false` truncates the file before writing the current run, which avoids accumulating stale rows when a config is rerun. Pair distinct configs with distinct paths (`fitting_summary_linear.csv`, `fitting_summary_poly2.csv`) when both use `append: false`.

The single-plot report now records `append`:

```json
"fitting_summary_csv": {
  "requested": true,
  "path": "reports/fitting_summary_linear.csv",
  "exists": true,
  "rows_written": 1,
  "append": false,
  "warnings": []
}
```

### Fitting batch sample

`configs/batch/fitting_batch_config.yaml` exercises both fit configs in one batch so the v0.8 `fit_artifact_summary` counters are non-zero in routine acceptance:

```powershell
py scripts\origin_batch_plot.py --batch-config configs\batch\fitting_batch_config.yaml
```

The batch report adds an `origin_session_summary` block alongside `fit_artifact_summary` to count retry usage across jobs.

### Cross-report artifact summary

`scripts/summarize_fit_artifacts.py` reads one or more single-plot or batch reports and writes `reports/origin_plot_v0_8_artifact_report.json` with deduplicated counts and per-artifact existence checks:

```powershell
py scripts\summarize_fit_artifacts.py --reports reports\origin_plot_v0_2_report.json reports\origin_plot_v0_3_batch_report.json
py scripts\summarize_fit_artifacts.py --reports-dir reports
```

The summary includes `summary_csv_outputs`, `residual_csv_outputs`, `residual_plot_outputs`, and a `missing_artifacts` list whenever the report-recorded path is no longer on disk. The aggregator never scans `output/` directly; it only reports the paths the source reports recorded.

### Status policy update

`PASS with session_retry` is treated as a passing status by the batch script, the artifact summarizer, and the single-plot exit code. The single-plot status precedence is:

1. `FAIL` if requested PNG/PDF/OPJU exports are missing.
2. `PARTIAL PASS` if some requested outputs are missing.
3. `PASS with warnings` for best-effort artifact issues (annotation, summary CSV, residuals, errorbar/fit overlay).
4. `PASS with session_retry` when retry was used to recover the Origin session.
5. `PASS` otherwise.

## v0.8.2 Retry Path Test and Session Profiles

v0.8.2 verifies the retry path with a deterministic test injection, lifts session settings into reusable profiles, and exposes session knobs on the CLI. No new fit models, layouts, or templates are introduced.

### `inject_session_error_once` (test-only)

```yaml
origin_session:
  inject_session_error_once: true
```

When `inject_session_error_once=true`, the script raises `InjectedSessionError` on the very first Origin pipeline attempt with the message `Injected test OriginExt ApplicationBase_LT_execute 无效指针`. The session classifier recognizes the message, retry kicks in, and the second attempt runs normally. The injection consumes itself, so a follow-up retry will not re-raise.

This is for verification of the retry path and must never be enabled in normal acceptance configs. The default is always `false`.

### Session profiles

```yaml
session_profile: "configs/sessions/default_session.yaml"
```

Session profiles live under `configs/sessions/` and contain the same fields as `origin_session`. Two profiles ship by default:

- `configs/sessions/default_session.yaml` — production-safe defaults (retries enabled, kill stale Origin enabled, no injection).
- `configs/sessions/test_retry_session.yaml` — test profile with `inject_session_error_once=true`.

Merge priority, lowest to highest:

1. Built-in defaults
2. `session_profile` settings
3. `origin_session` block in the plot config
4. CLI overrides

The plot report records `session_profile`, `session_profile_settings`, `cli_session_overrides`, and `effective_settings` so retry decisions are fully traceable.

### CLI session overrides

```powershell
py scripts\origin_plot_from_config.py --config <path> ^
    --session-max-retries 2 ^
    --session-retry-delay-seconds 1 ^
    --no-kill-stale-origin-before-retry ^
    --inject-session-error-once
```

Any flag omitted leaves the YAML/profile value untouched. `--inject-session-error-once` is the only CLI form for the test injection and inherits the same test-only constraint as the YAML field.

### Reports-dir artifact summarization

```powershell
py scripts\summarize_fit_artifacts.py --reports-dir reports
```

`--reports-dir` walks the directory's top-level `*.json` files, skips the artifact summary itself to avoid self-reference, and writes the same `reports/origin_plot_v0_8_artifact_report.json`. The output records `input_mode` (`reports`, `reports_dir`, or `mixed`) and `reports_dir` so consumers can tell how the summary was assembled.

### Session retry logic smoke test

```powershell
py scripts\test_session_retry_logic.py
```

This runs without Origin and verifies:

- Session error classifier accepts known Origin/COM messages and the injected error.
- Classifier rejects benign exceptions (`FileNotFoundError`, `ValueError`, `KeyError`, `TypeError`).
- `merge_session_settings` honors the profile → explicit → CLI priority chain.
- Defaults survive an empty merge.
- Out-of-range `max_retries`, `retry_delay_seconds`, and wrong-type fields are rejected.

A successful run prints `PASS: session retry logic smoke tests ok`.

### Retry-injected fitting config

`configs/fitting/linear_fit_retry_injected_config.yaml` exercises the retry path end-to-end:

```powershell
py scripts\validate_origin_plot_config.py --config configs\fitting\linear_fit_retry_injected_config.yaml
py scripts\origin_plot_from_config.py --config configs\fitting\linear_fit_retry_injected_config.yaml
```

Expected report: `status="PASS with session_retry"`, `attempts=2`, `retry_used=true`, `injection_triggered=true`, `final_session_status="ok_after_retry"`. PNG/PDF/OPJU outputs land under `output/origin_plot_fitting_retry_injected/`. The summary CSV is `reports/fitting_summary_linear_retry_injected.csv` so it does not collide with the regular linear baseline.

## v0.8.3 CLI Retry Smoke and Session History

v0.8.3 adds a CLI-driven retry smoke test, propagates injection metadata through batch and artifact reports, supports injection filtering in the artifact summarizer, and records session history for trend observation.

### CLI retry injection smoke test

```powershell
py scripts\test_cli_retry_injection.py
```

This script invokes `origin_plot_from_config.py` via subprocess with `--inject-session-error-once` and the standard linear config, then verifies the report shows `PASS with session_retry`, `retry_used=true`, `attempts=2`, `injection_triggered=true`, `final_session_status="ok_after_retry"`, and that `cli_session_overrides` is non-empty. It also checks PNG/PDF/OPJU existence.

### Aggregate smoke test runner

```powershell
py scripts\run_smoke_tests.py
```

Runs `test_session_retry_logic.py` and `test_cli_retry_injection.py` in sequence. Prints `PASS: all smoke tests passed` when both succeed; exits non-zero if any fails.

### Batch session_test_summary

The batch report now includes:

```json
"session_test_summary": {
  "jobs_with_retry_used": 0,
  "jobs_with_injection_triggered": 0,
  "jobs_with_cli_session_overrides": 0,
  "final_session_status_counts": {"ok": 2}
}
```

This lets higher-level workflows detect whether any batch job ran with injection or CLI overrides without opening individual job reports.

### Artifact summarizer injection filter

```powershell
py scripts\summarize_fit_artifacts.py --reports-dir reports --exclude-injection
py scripts\summarize_fit_artifacts.py --reports-dir reports --include-injection-only
```

- `--exclude-injection`: skips reports where `injection_triggered=true` or `inject_session_error_once=true`.
- `--include-injection`: explicitly includes injection reports (same as default, but marks `injection_filter="include_injection"` in output).
- `--include-injection-only`: includes only injection reports.
- Default: `injection_filter="include_all"`.

The artifact report records `injection_filter` so consumers know how the summary was assembled.

### Session history

Each single-plot run appends an entry to `reports/session_history.json`:

```json
[
  {
    "timestamp_utc": "2026-05-22T05:32:12Z",
    "config": "configs\\fitting\\linear_fit_config.yaml",
    "output_basename": "linear_fit",
    "status": "PASS",
    "retry_used": false,
    "attempts": 1,
    "injection_triggered": false,
    "final_session_status": "ok",
    "session_errors_count": 0
  }
]
```

The file grows indefinitely in v0.8.3; a future version may add `max_entries` truncation. If the file is corrupt, the script backs it up as `.bak` and rebuilds from scratch, recording a warning.

The single-plot report includes:

```json
"session_history": {
  "path": "reports/session_history.json",
  "updated": true,
  "entry_count_after_update": 5,
  "warnings": []
}
```

Streaks of `ok_after_retry` or `failed` entries in the history can flag a degrading Origin installation before it becomes a blocking failure.

## v0.8.4 Session History Health

v0.8.4 turns the v0.8.3 session history into a usable health observation: history grows with bounded retention, batch reports surface a recent-window health summary, the artifact summarizer can drop old reports via `--since`, and the smoke runner has an offline-only mode.

### `history_max_entries`

```yaml
origin_session:
  history_max_entries: 100
```

Defaults to 100. Range: 1–10000. `null` or `0` falls back to 100 silently to avoid unbounded files. The single-plot report records:

```json
"session_history": {
  "path": "reports/session_history.json",
  "updated": true,
  "entry_count_after_update": 100,
  "history_max_entries": 100,
  "truncated": true,
  "warnings": []
}
```

`truncated=true` means the file was longer than the limit and the oldest entries were dropped before write. The merge priority for `history_max_entries` is the same as the rest of `origin_session`: defaults < session profile < `origin_session` block < CLI overrides.

### Batch `session_history_summary`

The batch report adds:

```json
"session_history_summary": {
  "history_path": "reports/session_history.json",
  "entries_seen": 10,
  "recent_window": 20,
  "recent_ok": 7,
  "recent_ok_after_retry": 3,
  "recent_failed": 0,
  "recent_injection_triggered": 3,
  "health_status": "degraded"
}
```

`health_status` rules:

- `degraded` if any of the recent entries is `failed`, OR if `recent_ok_after_retry >= 3`.
- `unknown` if `reports/session_history.json` is missing or unreadable.
- `ok` otherwise.

The health status is a soft signal. Batch jobs themselves still PASS as long as Origin produces the requested artifacts.

### Artifact summary `--since`

```powershell
py scripts\summarize_fit_artifacts.py --reports-dir reports --exclude-injection --since 2000-01-01
```

`--since` accepts `YYYY-MM-DD` or full `YYYY-MM-DDTHH:MM:SSZ`. Reports without a top-level timestamp (current single-plot and batch reports) are kept by default and produce a warning. The artifact summary records `since` and `reports_skipped_by_since`.

### Smoke test modes

```powershell
py scripts\run_smoke_tests.py             # full local acceptance, requires Origin
py scripts\run_smoke_tests.py --skip-origin   # offline-only smoke tests
```

`--skip-origin` skips tests marked as requiring an Origin install (currently `test_cli_retry_injection`). The runner prints per-test exit codes and elapsed times in the summary block.

### Why session history is observation, not pass/fail

Session history is collected for trend analysis. A run with `health_status: degraded` does not flip the plot's status; a degraded health tells the operator to investigate the Origin install. The plot status is still `PASS`, `PASS with warnings`, `PASS with session_retry`, `PARTIAL PASS`, or `FAIL` based on actual artifacts and Origin pipeline outcomes. Only history-write-side failures land in `session_history.warnings`; they do not block plotting.

## YAML fields

- `input_file`: input data path, usually relative to this subproject.
- `input_format`: `auto`, `csv`, `xlsx`, `tsv`, `txt`, or `xls`.
- `sheet_name`: Excel sheet name or null.
- `x_column`: column to use as X.
- `y_columns`: one or more Y columns.
- `graph_type`: `line`, `scatter`, or `line_symbol`.
- `graph_title`, `x_title`, `y_title`: Origin graph and axis titles.
- `output_dir`: output directory.
- `output_basename`: base filename for requested exports.
- `show_origin`: show or hide Origin while automating.
- `save_opju`, `export_png`, `export_pdf`: requested output switches.
- `png_width`: PNG export width in pixels.
- `style_profile`: optional path to a reusable style YAML.
- `export_profile`: optional path to a reusable export YAML.
- `y_error_columns`: optional mapping from Y columns to Y error columns.
- `x_error_column`: optional X error column.
- `fitting`: optional Python-side linear or polynomial fitting configuration.

## Outputs

The v0.2 script writes requested outputs such as:

- `output/origin_plot_config/sample_origin_plot.png`
- `output/origin_plot_config/sample_origin_plot.pdf`
- `output/origin_plot_config/sample_origin_plot.opju`
- `reports/origin_plot_v0_2_report.json`
- `reports/origin_plot_v0_3_batch_report.json`
- `reports/origin_plot_v0_4_scan_report.json`

`output/` is generated and ignored by Git. The report uses relative paths so it can be committed when useful.

## Manual Gate / First-run Origin Dialog

This skill does not automate GUI clicking.

Origin may show first-run, license, update, or initialization dialogs. The user may need to manually confirm such dialogs once before automation can proceed normally.

In the current v0.2.1 validation, the user reported one initial OK dialog, but a later PowerShell rerun completed without a popup. Therefore this is documented as first-run manual initialization, not a recurring automation blocker.

If a dialog appears on every run, treat the result as PARTIAL PASS until Origin configuration is fixed.

## Common errors

- `ModuleNotFoundError: originpro`: install dependencies into Windows Python.
- `Please install PyYAML`: run `py -m pip install pyyaml`.
- `Origin Automation / COM smoke test failed`: start Origin once as the same user, repair Origin if needed, then rerun environment detection.
- `Missing column(s)`: update the YAML to match the data headers.
- `at least 2 valid numeric rows`: clean the selected X/Y columns or choose numeric columns.

## Roadmap

- More graph templates and style presets.
- Multi-layer and multi-panel Origin output.
- Batch plotting from a directory of configs.
- Optional style reference files for journal-specific figures.
