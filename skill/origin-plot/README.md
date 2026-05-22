# origin-plot

`origin-plot` is the Origin / OriginPro plot execution backend in this
repository. **Read `What it is NOT` before opening anything else.**

Current version: **v1.0.1 Core Execution Backend**.

---

## 1. What is origin-plot?

`origin-plot` is a stable Origin / OriginPro plot execution backend.

- **Input:** canonical CSV / XLSX / TSV / TXT data + an explicit YAML plot
  config.
- **Behavior:** validates the config, drives Origin / OriginPro through
  the verified executor, exports figures.
- **Output:** PNG, PDF, OPJU, and a portable `reports/report_package/`
  bundle.

That is the entire scope.

## 2. What it is NOT

`origin-plot` does **not** do any of the following. They belong to
**Codex** (or to a sibling Skill), upstream of this Skill:

- OCR
- Handwriting recognition
- Image / photo / screenshot data extraction
- Smart column-role inference
- Automatic graph-type recommendation
- Excel sheet auto-detection
- Excel header-row auto-detection
- Guessing user intent

The full list and the gating rules for tier-B candidates (grouped, multi-
panel, faceted, template reuse, OPJU/OTPU template execution) live in
[`contracts/non_goals.md`](contracts/non_goals.md).

> **origin-plot never infers; it executes explicit canonical config.**

## 3. Core boundary

```
┌────────────────────────┐    canonical CSV/XLSX +    ┌────────────────────────┐
│ Codex / Claude         │   explicit YAML config     │ origin-plot            │
│ (data understanding)   │ ─────────────────────────► │ (Origin execution)     │
│ messy Excel, Markdown, │                            │ validate, plot, export │
│ images, lab notebooks  │                            │ PNG / PDF / OPJU       │
└────────────────────────┘                            └────────────────────────┘
```

The contracts that define this boundary live in
[`contracts/`](contracts/README.md):

- [`canonical_data_contract.md`](contracts/canonical_data_contract.md)
- [`plot_config_schema.md`](contracts/plot_config_schema.md)
- [`codex_data_wrangler_contract.md`](contracts/codex_data_wrangler_contract.md)
- [`non_goals.md`](contracts/non_goals.md)

## 4. Quick start

From `skill/origin-plot/`:

```powershell
# Render one plot
py workflows\run_plot.py --config configs\examples\line_plot.yaml

# Render a batch
py workflows\run_batch.py --batch-config configs\examples\batch.yaml

# Run the minimal acceptance suite (3 examples + path leak scan)
py workflows\accept_core.py
```

A successful `accept_core.py` ends with `PASS: origin-plot core acceptance ok`.

## 5. Daily workflow for Codex / Claude

```
┌─ user gives Codex a messy artifact (Excel / Markdown / image / notebook)
│
├─ Codex stages the raw file under     data/raw/<dataset>.<ext>
├─ Codex writes canonical data to      data/cleaned/<dataset>.csv (or .xlsx)
├─ Codex writes the plot config to     configs/generated/<dataset>.yaml
├─ Codex invokes:                      py workflows\run_plot.py --config configs\generated\<dataset>.yaml
│
└─ Codex returns the deliverable from  reports/report_package/
```

Codex must satisfy the canonical data contract and the plot config schema
before invoking the workflow. `origin-plot` does not retry messy inputs;
it returns a validation error.

## 6. Output package

`reports/report_package/` is the primary deliverable. After a successful
run it contains:

```
reports/report_package/
  figures/<basename>.png
  figures/<basename>.pdf
  origin_projects/<basename>.opju
  configs/<config>.yaml
  figure_index.md      # human-readable index for the run
  run_report.json      # machine-readable run summary
```

`output/` contains the raw exports the executor produces. **`output/` is
git-ignored and must never be committed.** Reports must remain free of
absolute local paths (`H:\`, `C:\`, `E:\`, `/mnt/`); the hygiene scanner
in `ops/hygiene/` (or `scripts/check_committed_reports.py`) enforces this.

## 7. Directory map (one line each)

| Path | Role |
|---|---|
| [`core/`](core/) | Thin Python layer wrapping the verified v0.8.7 backend. Façade only; not a re-implementation. |
| [`workflows/`](workflows/README.md) | Daily entry-point CLIs (`run_plot.py`, `run_batch.py`, `accept_core.py`, `build_report_package.py`). |
| [`contracts/`](contracts/README.md) | Canonical data contract, plot config schema, Codex wrangler contract, non-goals. |
| [`configs/`](configs/) | YAML configs. `configs/examples/` ships worked examples; `configs/styles/`, `configs/exports/`, `configs/sessions/`, `configs/fitting/`, `configs/errorbar/`, `configs/batch/`, `configs/scan/`, `configs/generated/` are reusable profiles or generated artifacts. |
| [`data/`](data/) | `data/raw/` for messy upstream files, `data/cleaned/` for Codex output, `data/examples/` for shipped examples. |
| [`scripts/`](scripts/) | The verified v0.8.7 implementation. **Source of truth for Origin control.** Do not start here unless debugging. |
| [`ops/`](ops/README.md) | Advanced maintenance tooling (smoke tests, health, hygiene, release). Not part of daily flow. |
| [`archive/`](archive/README.md) | Documentation anchors for the v0.8.7 backend and the v0.9 smart-input experiment. |
| `reports/report_package/` | Primary deliverable. |
| `output/` | Raw exports. **Never commit.** |

A more navigational view lives in [`DIRECTORY.md`](DIRECTORY.md).

## 8. Version notes

- The verified v0.8.7 backend (Origin executor, validator, batch script,
  retry/health tooling, smoke tests) **remains in `scripts/`** and is the
  source of truth for Origin control. v1.0 did not re-implement it.
- v1.0-core-refactor introduced the public surface (`core/`, `workflows/`,
  `contracts/`, `ops/`). `core/` is a façade over `scripts/`. Full
  internalization belongs to v1.1+. Details:
  [`archive/v1_0_scope_clarification.md`](archive/v1_0_scope_clarification.md).
- v1.0.1-origin-plot-core-archive-notes added the v0.9 archive note,
  non-goals, and scope clarification.
- v0.9-origin-plot-smart-input is a historical experiment that is
  **preserved but not in the v1.0 mainline.** It lives at the
  `v0.9-origin-plot-smart-input` tag and the
  `archive/skill-v0.9-smart-input` branch. See
  [`archive/v0_9_smart_input_reference.md`](archive/v0_9_smart_input_reference.md).

## 9. Links

- Directory navigation: [`DIRECTORY.md`](DIRECTORY.md)
- Codex contract:
  [`contracts/README.md`](contracts/README.md),
  [`contracts/canonical_data_contract.md`](contracts/canonical_data_contract.md),
  [`contracts/plot_config_schema.md`](contracts/plot_config_schema.md),
  [`contracts/codex_data_wrangler_contract.md`](contracts/codex_data_wrangler_contract.md),
  [`contracts/non_goals.md`](contracts/non_goals.md)
- Operator entry points: [`workflows/README.md`](workflows/README.md)
- Maintenance tooling: [`ops/README.md`](ops/README.md)
- Historical anchors:
  [`archive/README.md`](archive/README.md),
  [`archive/v1_0_scope_clarification.md`](archive/v1_0_scope_clarification.md),
  [`archive/v0_9_smart_input_reference.md`](archive/v0_9_smart_input_reference.md),
  [`archive/v0_8_7_full_stack/README.md`](archive/v0_8_7_full_stack/README.md)

## 10. Hard rules

- No GUI auto-clicking. No `pyautogui`. No screenshot recognition. No
  mouse-coordinate clicks. No auto-clicking Origin dialogs.
- `output/` is generated; never commit it.
- Reports may not contain absolute local paths.
- All paths in configs and reports are relative to `skill/origin-plot/`.
- Behavior changes that touch Origin control land as `vX.Y` features in
  v1.x or later; the v1.0 line adds bookkeeping and documentation only.
