# CODEX — origin-plot operating guide

Engineering-execution guide for Codex when working on `origin-plot`.
Optimised for fewer explanations, more steps, and explicit canonical
output. Read [`skill/origin-plot/AGENT_USAGE.md`](AGENT_USAGE.md) first
for the shared boundary; this document only covers Codex specifics.

## 1. Mission

Take a messy upstream artifact. Produce:

1. A canonical CSV / XLSX under
   [`skill/origin-plot/data/cleaned/`](data/cleaned/).
2. An explicit YAML plot config under
   [`skill/origin-plot/configs/generated/`](configs/generated/).
3. A successful `py workflows\run_plot.py --config ...` run with all
   requested outputs in
   [`skill/origin-plot/reports/report_package/`](reports/report_package/).

Do **not** stop short of writing both the canonical CSV and the YAML.
Do **not** modify `origin-plot` source code. The Origin executor is
frozen at v0.8.7.

## 2. Never-do list

- Never invoke `py scripts\origin_plot_from_config.py` directly from a
  user-facing flow. Use
  [`skill/origin-plot/workflows/run_plot.py`](workflows/run_plot.py).
- Never edit anything under
  [`skill/origin-plot/scripts/`](scripts/),
  [`skill/origin-plot/core/`](core/), or
  [`skill/origin-plot/workflows/`](workflows/) Python files when
  satisfying a user request. They are frozen.
- Never add OCR, image extraction, smart column inference, header
  auto-detection, or graph-type recommendation to `origin-plot`. Those
  belong upstream of the workflow.
- Never use `pyautogui`, screenshot recognition, or mouse-coordinate
  automation. No GUI clicking on Origin dialogs.
- Never commit `skill/origin-plot/output/`. It is git-ignored.
- Never commit reports with absolute local paths (`H:\`, `C:\`, `E:\`,
  `/mnt/`).
- Never `git checkout v0.9-origin-plot-smart-input -- <path>` to read
  v0.9 files; that overwrites the v1.0 working tree. Use
  `git show <tag>:<path>` for read-only inspection or
  `git worktree add ../origin-plot-v0.9-view v0.9-origin-plot-smart-input`
  for a separate working tree.

## 3. Standard task flow

Run every command from `skill/origin-plot/`.

1. Stage the upstream artifact under `data/raw/`.

2. Read the artifact with `pandas`. Detect the sheet (when XLSX) and
   header row deterministically:

   ```python
   import pandas as pd
   df = pd.read_excel("data/raw/<file>.xlsx", sheet_name="<sheet>", header=0)
   ```

   - When the user has not named a sheet, list sheets with
     `pd.ExcelFile(...).sheet_names` and surface the choice. Do not
     guess silently.
   - When the header row is not row 0, set `header=` explicitly. Do
     not auto-search.

3. Clean the dataframe:

   - Strip column whitespace, unify column names, drop fully empty rows.
   - Coerce numeric columns with `pd.to_numeric(..., errors="raise")`
     so failures surface immediately.
   - Sort by the x-column when monotonicity matters; `origin-plot` does
     not sort.
   - Persist as UTF-8 CSV (no BOM):

     ```python
     df.to_csv("data/cleaned/<dataset>.csv", index=False, encoding="utf-8")
     ```

4. Write the YAML config to `configs/generated/<dataset>.yaml` using
   the template in section 6.

5. Validate, then plot:

   ```powershell
   py scripts\validate_origin_plot_config.py --config configs\generated\<dataset>.yaml
   py workflows\run_plot.py --config configs\generated\<dataset>.yaml
   ```

   `run_plot.py` already calls the validator internally; calling
   `validate_origin_plot_config.py` first is fast feedback when
   iterating.

6. Verify outputs on disk:

   - `reports/report_package/figures/<basename>.png`
   - `reports/report_package/figures/<basename>.pdf`
   - `reports/report_package/origin_projects/<basename>.opju`
   - `reports/report_package/figure_index.md`
   - `reports/report_package/run_report.json`

7. Run hygiene before staging:

   ```powershell
   py scripts\check_committed_reports.py
   ```

8. Stage only the files you intend to commit. Discard transient
   acceptance-side regenerations:

   ```powershell
   git checkout -- skill/origin-plot/reports/
   ```

## 4. Preferred output format (final reply)

When reporting back to the user, return a compact block in this order.
Use full repository-relative paths.

```
status: PASS | PASS with warnings | PASS with session_retry | FAIL
config: skill/origin-plot/configs/generated/<dataset>.yaml
data: skill/origin-plot/data/cleaned/<dataset>.csv
outputs:
  - skill/origin-plot/reports/report_package/figures/<basename>.png
  - skill/origin-plot/reports/report_package/figures/<basename>.pdf
  - skill/origin-plot/reports/report_package/origin_projects/<basename>.opju
report: skill/origin-plot/reports/report_package/run_report.json
warnings: <list, if any>
hygiene: skill/origin-plot/scripts/check_committed_reports.py PASS
notes: <one or two short lines>
```

Do not include screenshots. Do not paraphrase the YAML; cite the file.

## 5. Canonical CSV template

```csv
x,y
0,1.0
1,2.1
2,4.2
3,7.3
4,11.0
```

For uncertainty:

```csv
x,y,y_err
0,1.0,0.10
1,1.8,0.15
2,4.1,0.20
```

For multi-series, one column per series; `origin-plot` does not pivot:

```csv
x,y_a,y_b
0,1.0,2.0
1,2.1,3.9
2,4.2,7.8
```

## 6. Canonical YAML template

```yaml
input_file: "data/cleaned/<dataset>.csv"
input_format: "auto"          # csv | xlsx | tsv | txt | xls | auto
sheet_name: null              # only for XLSX

x_column: "x"
y_columns:
  - "y"

graph_type: "line"            # line | scatter | line_symbol | errorbar
graph_title: "<title>"
x_title: "X"
y_title: "Y"

style_profile: "configs/styles/lab_report_style.yaml"
export_profile: "configs/exports/default_export.yaml"

output_dir: "output/<run-name>"
output_basename: "<basename>"

show_origin: true
```

Errorbar block (added when `graph_type: errorbar`):

```yaml
y_error_columns:
  y: "y_err"
x_error_column: null
```

Fit overlay block (mirror
[`skill/origin-plot/configs/examples/fitting_plot.yaml`](configs/examples/fitting_plot.yaml)):

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

## 7. Batch command

For multi-job batches, write a batch YAML referencing existing
single-plot configs:

```yaml
batch_name: "<name>"
continue_on_error: true
jobs:
  - name: "<job-1>"
    config: "configs/generated/<dataset-1>.yaml"
  - name: "<job-2>"
    config: "configs/generated/<dataset-2>.yaml"
```

Run:

```powershell
py workflows\run_batch.py --batch-config configs\generated\<batch>.yaml
```

The verified v0.8.7 batch script
([`skill/origin-plot/scripts/origin_batch_plot.py`](scripts/origin_batch_plot.py))
remains available when you need richer batch reports
(`session_history_summary`, `fit_artifact_summary`, retry rollups).

## 8. Maintenance commands

Use these only for debugging or release hygiene; they are not part of
a daily plot flow.

```powershell
# fast self-check on the three example configs + path leak scan
py workflows\accept_core.py

# offline smoke runner (no Origin)
py ops\smoke\run_smoke_tests.py --skip-origin

# session history reset
py ops\health\reset_session_history.py

# pre-commit shell (Windows)
powershell -ExecutionPolicy Bypass -File ops\release\pre_commit_smoke.ps1

# cross-batch fit-artifact rollup
py ops\reports\summarize_fit_artifacts.py --reports-dir reports --exclude-injection --since 2000-01-01 --drop-missing-timestamp
```

## 9. v0.9 smart-input — read-only

If a task asks "what did v0.9 do for X?", inspect read-only:

```powershell
git show v0.9-origin-plot-smart-input:skill/origin-plot/scripts/analyze_data_source.py
git worktree add ../origin-plot-v0.9-view v0.9-origin-plot-smart-input
```

Do **not** copy v0.9 code into the v1.0 mainline. Smart-input belongs to
a sibling Skill, not to `skill/origin-plot/`. See
[`skill/origin-plot/archive/v0_9_smart_input_reference.md`](archive/v0_9_smart_input_reference.md).

## 10. Cross-links

- Shared boundary:
  [`skill/origin-plot/AGENT_USAGE.md`](AGENT_USAGE.md).
- Claude guide:
  [`skill/origin-plot/CLAUDE.md`](CLAUDE.md).
- Codex contract:
  [`skill/origin-plot/contracts/codex_data_wrangler_contract.md`](contracts/codex_data_wrangler_contract.md).
- YAML schema:
  [`skill/origin-plot/contracts/plot_config_schema.md`](contracts/plot_config_schema.md).
- Daily entry surface:
  [`skill/origin-plot/workflows/README.md`](workflows/README.md).
- Onboarding test:
  [`skill/origin-plot/AGENT_ONBOARDING_TEST.md`](AGENT_ONBOARDING_TEST.md).
