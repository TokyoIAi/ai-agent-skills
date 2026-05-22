# origin-plot

`origin-plot` is the Origin / OriginPro plot execution backend in this
repository. **It is not a data understanding tool.** Codex (or any
equivalent caller) is responsible for cleaning input, normalising columns,
and choosing the plot intent. `origin-plot` then receives canonical data and
a YAML config, and reliably renders PNG / PDF / OPJU through Origin.

Current version: **v1.0-core-refactor**.

## What it does

- Validates a plot YAML against the v1.0 schema.
- Loads canonical CSV / XLSX / TSV / TXT data via `core/data_loader.py`.
- Drives Origin / OriginPro through the verified executor that ships in
  `scripts/`.
- Exports PNG / PDF / OPJU.
- Assembles `reports/report_package/` with figures, OPJU, configs,
  `figure_index.md`, and `run_report.json`.

## What it does not do

- **No** image OCR, handwriting recognition, or photo-of-table parsing.
- **No** auto-inference of user intent.
- **No** Markdown / OPJU / image input formats.
- **No** grouped / multi-panel / faceted plots in the v1.0 core.
- **No** GUI clicking, screenshot recognition, or mouse-coordinate
  automation.

If a request needs any of the above, hand it to Codex. Codex cleans the
data, writes the canonical CSV / XLSX, and writes the YAML; `origin-plot`
then runs.

## Three day-to-day commands

From `skill/origin-plot/`:

### 1. Render a single plot

```powershell
py workflows\run_plot.py --config configs\examples\line_plot.yaml
```

### 2. Render a batch

```powershell
py workflows\run_batch.py --batch-config configs\examples\batch.yaml
```

### 3. Codex-driven workflow

```text
Codex reads the user's raw / messy artifact (Excel, Markdown, image, etc.)
Codex writes data/cleaned/<dataset>.csv (canonical shape)
Codex writes configs/generated/<dataset>.yaml (v1.0 schema)
origin-plot runs:  py workflows\run_plot.py --config configs\generated\<dataset>.yaml
```

The full contract lives in
[`contracts/codex_data_wrangler_contract.md`](contracts/codex_data_wrangler_contract.md).

## Outputs

`reports/report_package/` is the primary deliverable. After a successful
run it contains:

```
reports/report_package/
  figures/<basename>.png
  figures/<basename>.pdf
  origin_projects/<basename>.opju
  configs/<config>.yaml
  figure_index.md
  run_report.json
```

`output/` contains the raw exports the executor produces. **`output/` is
git-ignored and must never be committed.**

## Layout

| Path | Role |
|---|---|
| `core/` | Thin Python layer that wraps the verified v0.8.7 implementation. |
| `workflows/` | Public CLIs (`run_plot.py`, `run_batch.py`, `accept_core.py`, `build_report_package.py`). |
| `contracts/` | Canonical data contract, plot config schema, Codex wrangler contract. |
| `configs/examples/` | Worked examples (`line_plot.yaml`, `errorbar_plot.yaml`, `fitting_plot.yaml`, `batch.yaml`). |
| `data/examples/` | Tiny canonical datasets used by the examples. |
| `data/raw/` | Where Codex stages messy upstream files (git-ignored when bulky). |
| `data/cleaned/` | Where Codex writes canonical CSV / XLSX before invoking workflows. |
| `scripts/` | The verified v0.8.7 implementation. Still functional; `core/` and `ops/` delegate here. |
| `ops/` | Advanced maintenance tooling (smoke tests, health, hygiene, release). Not part of daily flow. |
| `archive/v0_8_7_full_stack/` | Documentation anchor for the v0.8.7 surface that v1.0 keeps verbatim. |
| `reports/report_package/` | Primary deliverable after every run. |

## Acceptance

Run all three example configs plus a hygiene scan:

```powershell
py workflows\accept_core.py
```

Expected: `PASS: origin-plot core acceptance ok`.

## Maintenance tools (ops)

`ops/` is for operators who need the v0.8.7 stability tooling. None of these
commands are required for daily plotting.

```powershell
# Run offline / full smoke tests:
py ops\smoke\run_smoke_tests.py --skip-origin
py ops\smoke\run_smoke_tests.py

# Pre-commit hygiene (offline smoke + report path leak scan):
powershell -ExecutionPolicy Bypass -File ops\release\pre_commit_smoke.ps1
bash ops/release/pre_commit_smoke.sh

# Inspect or reset session health:
py ops\health\reset_session_history.py
py ops\health\test_session_health_logic.py

# Cross-report fit-artifact rollup:
py ops\reports\summarize_fit_artifacts.py --reports-dir reports --exclude-injection --since 2000-01-01 --drop-missing-timestamp

# Path leak scanner:
py ops\hygiene\check_committed_reports.py
```

Each `ops/` script delegates to the verified script in `scripts/`. See
`ops/README.md`.

## Hard rules

- No GUI auto-clicking. No `pyautogui`. No screenshot recognition. No
  mouse-coordinate clicks. No auto-clicking Origin dialogs.
- `output/` is generated; never commit it.
- Reports may not contain absolute local paths (`H:\`, `C:\`, `E:\`,
  `/mnt/`). The hygiene scanner enforces this.
- All paths in configs and reports are relative to `skill/origin-plot/`.
- Behavior changes that touch Origin control land as `vX.Y` features; the
  v1.0 core layer adds bookkeeping only.

## Migration notes

- Daily users: switch to `workflows/run_plot.py` and the four
  `configs/examples/*.yaml` files.
- Operators that relied on `scripts/...` directly: nothing breaks; the same
  scripts still work and `ops/` exposes the same entries.
- Documentation references that pointed to v0.8.7 health-monitoring CLIs
  should now use `ops/health/` paths.
- The image / OCR / Markdown smart-input experiments that lived on the
  `skill` branch (tag `v0.9-origin-plot-smart-input`) are intentionally
  **not** part of v1.0. Codex absorbs those responsibilities.
