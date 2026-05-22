# origin-plot

`origin-plot` is a Codex Agent Skill for reproducible scientific plotting with Windows Python, `originpro`, and local Origin / OriginPro. It uses API automation, not GUI clicking, screenshot recognition, or mouse-coordinate automation.

Current version: v0.9.

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

## v0.8.5 Timestamp and Health Policy

v0.8.5 stamps every report with `timestamp_utc`, exposes a session-health policy in profiles, gives operators a way to clear history before a clean acceptance pass, and lets the artifact summarizer drop reports without timestamps.

### Report timestamps

Every report writes a top-level `timestamp_utc` field in `YYYY-MM-DDTHH:MM:SSZ` form:

- `reports/origin_plot_v0_2_report.json` (single-plot)
- `reports/origin_plot_v0_3_batch_report.json` (batch)
- `reports/origin_plot_v0_4_scan_report.json` (directory scan)
- `reports/origin_plot_v0_8_artifact_report.json` (artifact summary)

### `--reset-session-history` and `reset_session_history.py`

Two equivalent ways to clear `reports/session_history.json` before a clean health observation window:

```powershell
py scripts\origin_plot_from_config.py --config <config> --reset-session-history
py scripts\reset_session_history.py
```

Both back up the existing file to `reports/session_history.bak.json` (overwriting any prior backup) and write `[]` to the live file. The single-plot report records `session_history.reset_before_run` so the action is traceable.

### Session health policy

`origin_session.health` (or the `health` block in a session profile) controls the soft health signal:

```yaml
session_profile_name: "default_session"
retry_on_com_error: true
max_retries: 1
kill_stale_origin_before_retry: true
retry_delay_seconds: 2
inject_session_error_once: false
history_max_entries: 100
health:
  recent_window: 20
  degraded_ok_after_retry_threshold: 3
  degraded_failed_threshold: 1
```

Validator rules:

- `recent_window`: integer 1–10000.
- `degraded_ok_after_retry_threshold`: integer 0–10000.
- `degraded_failed_threshold`: integer 0–10000.

Status rules in `session_history_summary`:

- `recent_failed >= degraded_failed_threshold` → `degraded`.
- `recent_ok_after_retry >= degraded_ok_after_retry_threshold` → `degraded`.
- otherwise → `ok`.
- history file missing or unreadable → `unknown`.

The status is still a soft signal; plot pass/fail is unchanged.

### `--drop-missing-timestamp`

```powershell
py scripts\summarize_fit_artifacts.py --reports-dir reports --exclude-injection --since 2000-01-01 --drop-missing-timestamp
```

When `--since` is active, this flag drops reports without `timestamp_utc` instead of keeping them with a warning. The artifact report records `drop_missing_timestamp` and `reports_skipped_missing_timestamp`.

### Pre-commit smoke

```powershell
powershell -ExecutionPolicy Bypass -File scripts\pre_commit_smoke.ps1
bash scripts/pre_commit_smoke.sh
```

Manually invoked offline guard. It runs `run_smoke_tests.py --skip-origin` and exits non-zero if any offline smoke test fails. The script does not install Git hooks; teams may wire it into their preferred guard.

### Why health stays a soft signal

Health is meant to surface trends in the Origin install. A degraded streak indicates upcoming issues but should never invalidate a successful plot run. Plot pass/fail depends only on actual outputs, retries, and pipeline outcomes — never on the health observation.

## v0.8.6 Operator Health UX

v0.8.6 makes session health observable per single run, lets operators tune thresholds without editing YAML, rolls health up across reports, and documents the contributor workflow.

### Health policy CLI overrides

```powershell
py scripts\origin_plot_from_config.py --config <config> ^
    --health-recent-window 5 ^
    --health-degraded-ok-after-retry-threshold 2 ^
    --health-degraded-failed-threshold 1
```

CLI overrides have the highest priority (defaults < session_profile < `origin_session` < CLI). Validation rules:

- `--health-recent-window`: integer 1–10000.
- `--health-degraded-ok-after-retry-threshold`: integer 0–10000.
- `--health-degraded-failed-threshold`: integer 0–10000.

Threshold = 0 is allowed and produces a more sensitive degraded check (any matching event flips `health_status` to `degraded`).

The single-plot report records:

```json
"origin_session": {
  "health_policy_overrides": {
    "recent_window": 5,
    "degraded_ok_after_retry_threshold": 2,
    "degraded_failed_threshold": 1
  },
  "effective_settings": {
    "health": {
      "recent_window": 5,
      "degraded_ok_after_retry_threshold": 2,
      "degraded_failed_threshold": 1
    }
  }
}
```

### Single-plot `session_health_snapshot`

Every single-plot report carries a snapshot computed after the new history entry is written:

```json
"session_health_snapshot": {
  "history_path": "reports/session_history.json",
  "entries_seen": 2,
  "recent_window": 20,
  "degraded_ok_after_retry_threshold": 3,
  "degraded_failed_threshold": 1,
  "recent_ok": 2,
  "recent_ok_after_retry": 0,
  "recent_failed": 0,
  "recent_injection_triggered": 0,
  "health_status": "ok"
}
```

`health_status` is one of `ok`, `degraded`, or `unknown` (history missing or unreadable). Operators see health right after each run instead of waiting for the next batch.

### Artifact summary `health_status_counts`

`summarize_fit_artifacts.py` now rolls up health across reports:

```json
"health_status_counts": {"ok": 2, "degraded": 0, "unknown": 0},
"reports_with_health_status": 2,
"reports_without_health_status": 1
```

Batch reports contribute via `session_history_summary.health_status`; single-plot reports contribute via `session_health_snapshot.health_status`. Reports without either field count under `reports_without_health_status` (typical for legacy single-plot or scan reports).

### Contributor workflow

A new repository-level `CONTRIBUTING.md` documents:

- Project scope and branch rule.
- Skill layout, safety rules, output/ ban.
- Pre-commit smoke routine (`run_smoke_tests.py --skip-origin`).
- Pre-tag full acceptance routine.
- How to add new smoke tests and register them in `run_smoke_tests.py`.
- `vX.Y` vs `vX.Y.Z` versioning convention.

### Health is advisory

`health_status` is still a soft signal. A `degraded` snapshot does not flip plot status. The plot pass/fail decision is based purely on artifacts, retries, and pipeline outcomes.

## v0.8.7 Release Hygiene

v0.8.7 closes the v0.8.x series with release-discipline tooling: a committed-report path scanner, a CI-friendly health echo, and a small refactor that lets batch and single-plot reports share one health computation. After v0.8.7 the v0.8.x line is frozen for real-usage observation; new plotting features wait for v0.9.

### `check_committed_reports.py`

```powershell
py scripts\check_committed_reports.py
py scripts\check_committed_reports.py --reports-dir reports
py scripts\check_committed_reports.py --include-bak
```

Scans `reports/*.json|*.csv|*.md|*.txt` for absolute path leaks (`H:\`, `C:\`, `E:\`, `H:/`, `C:/`, `H:\\` JSON-escaped form, and POSIX `/mnt/`). Prints `PASS: committed report path check ok` and exits 0 when clean. On detection, prints offending file/line/snippet and exits 1.

`session_history.bak.json` and `*.bak` are skipped by default; pass `--include-bak` to scan them too.

### Pre-commit smoke now includes the path check

`pre_commit_smoke.ps1` and `pre_commit_smoke.sh` now run two steps:

1. `run_smoke_tests.py --skip-origin`
2. `check_committed_reports.py`

Either failure aborts the guard with exit code 1.

### `--print-health`

```powershell
py scripts\origin_plot_from_config.py --config <config> --print-health
```

After the report is written, the script prints one machine-readable line:

```
HEALTH_SNAPSHOT_JSON: {"degraded_failed_threshold": 1, "degraded_ok_after_retry_threshold": 3, ...}
```

Shell or CI consumers can extract the JSON and assert on `health_status` directly. When no snapshot is available the line carries `{"health_status": "unknown"}`. The line never includes absolute paths.

### Batch health refactor

`origin_batch_plot.py` now sources `session_history_summary` from the shared `compute_health_snapshot` helper in `origin_session_utils.py`. Field names and semantics are unchanged. Single-plot and batch reports now share one source of truth for health computation.

### v0.8.x freeze policy

After v0.8.7, the v0.8.x line is frozen pending real-usage observation. Bug fixes during the freeze land as `v0.8.7-hotfix-N` if absolutely necessary. New plotting features (multi-series fitting, color profiles, `.otpu` template reuse, multi-panel layouts) target v0.9 and require a clean stretch of `health_status="ok"` runs in production before development starts.

## v0.9 Smart Data Understanding + Auto Plot

v0.9 introduces a smart-input front end. Hand the Skill a CSV / XLSX / TSV / TXT / Markdown table; it analyzes structure, infers column roles, recommends a graph type, generates a v0.2-compatible plot config, and reuses the existing Origin pipeline to render PNG / PDF / OPJU.

### Supported smart inputs

- CSV (`*.csv`)
- TSV (`*.tsv`)
- TXT delimited text (`*.txt`)
- Excel (`*.xlsx`) with auto-sheet selection
- Markdown table (`*.md`, first standard `| ... |` table extracted)

Markdown inputs are converted to a CSV bridge under `data/smart_inputs/_bridges/<basename>.csv` so the existing Origin pipeline can consume them as plain CSV. The bridge file is reported back via `plot_input_path` in the analysis report.

### Smart input config

```yaml
input_file: "data/smart_inputs/sample_markdown_table.md"
input_format: "auto"

smart_analysis:
  enabled: true
  detect_header_row: true
  detect_units: true
  detect_column_roles: true
  detect_plot_type: true

role_inference_rules:
  prefer_first_numeric_as_x: true
  prefer_remaining_numeric_as_y: true
  infer_error_columns_by_suffix: true
  infer_group_columns_by_text: true
  error_column_suffixes: ["_err", "_error", "_uncertainty", "误差", "标准差"]
  x_column_candidates: ["x", "time", "时间", "distance", "距离"]
  group_column_candidates: ["group", "类别", "组别", "type"]

markdown:
  extract_first_table: true

excel:
  auto_detect_sheet: true
  auto_detect_header_row: true

output:
  generated_config_path: "configs/generated/smart_generated_plot_config.yaml"
  smart_report_path: "reports/smart_input_analysis_report.json"
  output_dir: "output/origin_plot_smart"
  output_basename: null   # auto-derived from input filename when null
  style_profile: "configs/styles/lab_report_style.yaml"
  export_profile: "configs/exports/default_export.yaml"
  show_origin: true
  report_package_dir: "reports/report_package"
```

### Role inference rules

- **x**: explicit candidate match (case-insensitive name without unit suffix) wins; otherwise the first numeric column.
- **y**: every remaining numeric column that is not an `x` and not an inferred error column.
- **y_error**: any numeric column whose name ends in one of `error_column_suffixes` and whose base name matches a y candidate.
- **group**: any text column whose name appears in `group_column_candidates`; falls back to the first text column when none match.

### Recommended graph type

- `x` + single y → `line`
- `x` + y + y_error → `errorbar`
- `x` + group + value → `grouped_line` (pivoted to wide form before plotting)
- Anything else → falls back to `scatter` with a warning.

### Workflow

```powershell
py scripts\analyze_data_source.py --config configs\smart\smart_input_config.yaml
py scripts\run_smart_plot.py --config configs\smart\smart_input_config.yaml
```

`analyze_data_source.py` only inspects the data; it never calls Origin. `run_smart_plot.py` runs the analyzer and then invokes `origin_plot_from_config.py` against the generated config to produce PNG/PDF/OPJU.

Override the input without editing the config:

```powershell
py scripts\run_smart_plot.py --config configs\smart\smart_input_config.yaml --input-file data/smart_inputs/sample_grouped.csv
```

### Grouped plot MVP

`graph_type: grouped_line` and `graph_type: grouped_scatter` accept `group_column` plus a single value column. Both validator and plotting script pivot to wide form (one column per group level) before sending to Origin, then render as multiple line or scatter series. Errorbars and fitting are not paired with grouped data in v0.9; the existing line/scatter/errorbar/fitting paths remain untouched.

### Report package output

After a successful smart run, `reports/report_package/` collects portable artifacts:

```
reports/report_package/
  figures/<basename>.png, .pdf
  origin_projects/<basename>.opju
  configs/smart_generated_plot_config.yaml
  figure_index.md
  run_report.json
```

`figure_index.md` lists `input_file`, detected roles, recommended graph type, and the relative paths to the produced files. `run_report.json` mirrors the smart-run report with relative paths only. The package never copies anything from `output/` other than the latest run's outputs.

### What v0.9 does not do

- No image / OCR pipeline. Image-based input recognition is reserved for a future `v0.9.x experimental` slot. Stub fields may exist in reports, but image-driven runs are not part of v0.9 acceptance.
- No multi-panel layouts.
- No additional fit models or color profiles.
- No `.otpu` template reuse.

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
