# AGENT_USAGE — origin-plot

This is the shared operating guide for any agent (Codex, Claude, or
another LLM-driven assistant) working on top of `origin-plot`.

Read this **before** [`skill/origin-plot/CODEX.md`](CODEX.md) or
[`skill/origin-plot/CLAUDE.md`](CLAUDE.md). The role-specific guides
assume you already know everything below.

If you have just landed in this repository, also read:

- [`skill/origin-plot/README.md`](README.md) — the user-facing overview.
- [`skill/origin-plot/DIRECTORY.md`](DIRECTORY.md) — the directory map.
- [`skill/origin-plot/contracts/README.md`](contracts/README.md) — the
  data and config contract.
- [`skill/origin-plot/AGENT_ONBOARDING_TEST.md`](AGENT_ONBOARDING_TEST.md)
  — the 60-second comprehension test.

## 1. Role boundary

```
┌────────────────────────────┐    canonical CSV/XLSX +    ┌────────────────────────────┐
│ Agent (Codex / Claude)     │   explicit YAML config     │ origin-plot                │
│ data understanding         │ ─────────────────────────► │ Origin execution           │
│ messy Excel / Markdown /   │                            │ validate, plot, export     │
│ image / lab notebook       │                            │ PNG / PDF / OPJU + report  │
└────────────────────────────┘                            └────────────────────────────┘
```

- **You** own data understanding upstream of `origin-plot`. That means
  reading messy Excel, deciding which sheet and which header row, naming
  columns sensibly, picking a graph type, writing the YAML config.
- **`origin-plot`** owns Origin / OriginPro execution. It validates the
  YAML, drives Origin, exports PNG / PDF / OPJU, and assembles
  [`skill/origin-plot/reports/report_package/`](reports/report_package/).
- The boundary is **explicit canonical CSV / XLSX + explicit YAML**. If
  you cannot produce both, do not invoke the workflow. Stop and ask.

The full contract lives in:

- [`skill/origin-plot/contracts/canonical_data_contract.md`](contracts/canonical_data_contract.md)
- [`skill/origin-plot/contracts/plot_config_schema.md`](contracts/plot_config_schema.md)
- [`skill/origin-plot/contracts/codex_data_wrangler_contract.md`](contracts/codex_data_wrangler_contract.md)
- [`skill/origin-plot/contracts/non_goals.md`](contracts/non_goals.md)

## 2. Do-not-do list

`origin-plot` deliberately refuses to do any of these. If a request
implies one of them, the work belongs upstream of the workflow, not
inside it.

- **Do not** add OCR, handwriting recognition, or image / photo /
  screenshot data extraction.
- **Do not** infer column roles. The YAML config must list `x_column`
  and `y_columns` explicitly.
- **Do not** auto-detect the Excel sheet or header row. The YAML config
  must set `sheet_name` (when needed) and the upstream cleaning step
  must produce a header row at row 1.
- **Do not** auto-recommend graph types. The YAML config must set
  `graph_type` explicitly.
- **Do not** guess user intent. If something is unclear, write the
  question down and stop.
- **Do not** use GUI automation. No `pyautogui`, no screenshot
  recognition, no mouse-coordinate clicks, no auto-clicking Origin
  dialogs.
- **Do not** modify the Origin control logic. The Origin executor is
  frozen at v0.8.7. Behavior changes land as v1.x feature releases.
- **Do not** commit `skill/origin-plot/output/`. It is generated and
  git-ignored.
- **Do not** commit reports that contain absolute local paths (`H:\`,
  `C:\`, `E:\`, `/mnt/`). The hygiene scanner blocks them.
- **Do not** revive v0.9 smart-input under `skill/origin-plot/`. Future
  smart-input work belongs to a sibling Skill.

The complete tier A / tier B list is in
[`skill/origin-plot/contracts/non_goals.md`](contracts/non_goals.md).

## 3. Standard workflow

Run every command from `skill/origin-plot/`.

1. Stage the upstream artifact under
   [`skill/origin-plot/data/raw/`](data/raw/).
2. Read the artifact, decide the canonical structure, write a clean
   table to [`skill/origin-plot/data/cleaned/<dataset>.csv`](data/cleaned/)
   (or `.xlsx`).
3. Write the YAML plot config to
   [`skill/origin-plot/configs/generated/<dataset>.yaml`](configs/generated/)
   using the canonical schema. Reference a style profile from
   [`skill/origin-plot/configs/styles/`](configs/styles/) and an export
   profile from [`skill/origin-plot/configs/exports/`](configs/exports/)
   when appropriate.
4. Render the plot:

   ```powershell
   py workflows\run_plot.py --config configs\generated\<dataset>.yaml
   ```

5. Collect the deliverable from
   [`skill/origin-plot/reports/report_package/`](reports/report_package/):
   `figures/<basename>.png`, `figures/<basename>.pdf`,
   `origin_projects/<basename>.opju`, `figure_index.md`,
   `run_report.json`.

For batches, drive multiple jobs through one batch YAML:

```powershell
py workflows\run_batch.py --batch-config configs\examples\batch.yaml
```

For a fast self-check after editing YAML examples or configs:

```powershell
py workflows\accept_core.py
```

A passing run ends with `PASS: origin-plot core acceptance ok`.

## 4. Minimal canonical CSV

UTF-8, no BOM, single header row, numeric columns coerce cleanly via
`pandas.to_numeric`, sorted by `x` if monotonicity matters.

```csv
x,y
0,1.0
1,2.1
2,4.2
3,7.3
4,11.0
```

For uncertainty add an error column. The convention is `<y>_err`:

```csv
x,y,y_err
0,1.0,0.10
1,1.8,0.15
2,4.1,0.20
```

Error columns must be non-negative.

## 5. Minimal YAML config

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

For an errorbar plot:

```yaml
graph_type: "errorbar"
y_error_columns:
  y: "y_err"
```

For a fit overlay, follow the `fitting:` block in
[`skill/origin-plot/configs/examples/fitting_plot.yaml`](configs/examples/fitting_plot.yaml).
The full schema is in
[`skill/origin-plot/contracts/plot_config_schema.md`](contracts/plot_config_schema.md).

## 6. Validation checklist (before invoking the workflow)

- [ ] The CSV / XLSX path under `data/cleaned/` exists and is UTF-8.
- [ ] The header row sits on row 1 of the file.
- [ ] Every column listed in `x_column` and `y_columns` appears in the
      header.
- [ ] Every numeric column converts cleanly via `pandas.to_numeric`.
- [ ] If `graph_type: errorbar`, every key in `y_error_columns` is in
      `y_columns` and every error column is non-negative.
- [ ] `graph_type` is one of the supported values
      (`line`, `scatter`, `line_symbol`, `errorbar`).
- [ ] `output_dir` is a relative path under
      [`skill/origin-plot/output/`](output/).
- [ ] No absolute local paths (`H:\`, `C:\`, `E:\`, `/mnt/`) appear
      anywhere in the YAML.

If any item fails, fix the upstream data or the YAML. Do **not** rerun
the workflow on broken inputs.

## 7. Failure policy

- **Validation error** — `run_plot.py` exits non-zero with a clear
  message. Fix the YAML or the canonical CSV. Do not retry blindly.
- **Origin transient error** (`无效指针 / invalid pointer`, COM startup
  failure) — the v0.8.x retry path handles single-attempt retries
  automatically. If retries do not converge, kill stale Origin
  processes and rerun:

  ```powershell
  Get-Process Origin64 -ErrorAction SilentlyContinue | Stop-Process -Force
  py workflows\run_plot.py --config <config>
  ```

- **`PASS with warnings`** — accept it; the requested PNG / PDF / OPJU
  exist. Surface the warnings in your final report.
- **`PASS with session_retry`** — same: accept it, surface the retry in
  your final report.
- **Hygiene scan failure** — the path leak scanner found an absolute
  local path in `reports/`. Fix the offending report; never strip
  `reports/` from version control to bypass the scanner.

## 8. After every run

- Confirm `reports/report_package/figures/<basename>.png`,
  `reports/report_package/figures/<basename>.pdf`, and
  `reports/report_package/origin_projects/<basename>.opju` all exist.
- Confirm `reports/report_package/figure_index.md` and
  `reports/report_package/run_report.json` are up to date.
- Run [`skill/origin-plot/scripts/check_committed_reports.py`](scripts/check_committed_reports.py)
  before staging any change in `reports/` for commit.
- Discard transient acceptance-side regenerations of `reports/` you do
  not intend to keep:

  ```powershell
  git checkout -- skill/origin-plot/reports/
  ```

- Never commit anything under
  [`skill/origin-plot/output/`](output/).

## 9. Cross-links

- Role-specific guides:
  [`skill/origin-plot/CODEX.md`](CODEX.md),
  [`skill/origin-plot/CLAUDE.md`](CLAUDE.md).
- Onboarding test:
  [`skill/origin-plot/AGENT_ONBOARDING_TEST.md`](AGENT_ONBOARDING_TEST.md).
- Daily entry surface:
  [`skill/origin-plot/workflows/README.md`](workflows/README.md).
- Codex contract:
  [`skill/origin-plot/contracts/README.md`](contracts/README.md),
  [`skill/origin-plot/contracts/codex_data_wrangler_contract.md`](contracts/codex_data_wrangler_contract.md).
- Hard non-goals:
  [`skill/origin-plot/contracts/non_goals.md`](contracts/non_goals.md).
- v1.0 scope:
  [`skill/origin-plot/archive/v1_0_scope_clarification.md`](archive/v1_0_scope_clarification.md).
- v0.9 archive:
  [`skill/origin-plot/archive/v0_9_smart_input_reference.md`](archive/v0_9_smart_input_reference.md).
