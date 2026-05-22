# v1.0-core-refactor scope clarification

This note records what `v1.0-origin-plot-core-refactor` actually delivered
and what it deliberately did **not** deliver. It exists so that future
maintainers do not assume `core/` already owns the Origin control logic.

## What v1.0-core-refactor is

A **public surface refactor**. The new layout adds:

- `workflows/` — public CLIs (`run_plot.py`, `run_batch.py`,
  `accept_core.py`, `build_report_package.py`).
- `core/` — a thin Python layer in front of the verified v0.8.7
  implementation.
- `contracts/` — canonical data contract, plot config schema, Codex
  data-wrangler contract, this scope clarification, and the non-goals
  document.
- `configs/examples/` — worked examples (`line_plot.yaml`,
  `errorbar_plot.yaml`, `fitting_plot.yaml`, `batch.yaml`).
- `data/examples/` — minimal canonical datasets used by the examples.
- `ops/` — categorised re-exports of the v0.8.7 maintenance scripts
  (smoke tests, health, hygiene, release).
- `archive/` — documentation anchors for the v0.8.7 surface and the v0.9
  smart-input experiment.
- `data/raw/`, `data/cleaned/` — drop-points for Codex's data wrangling
  workflow.
- Updated `README.md` and `SKILL.md`.

## What v1.0-core-refactor is not

A re-implementation of Origin control. The verified v0.8.7
implementation continues to live in `scripts/`. v1.0 wraps it; it does
not replace it.

## Honest module accounting

This is the section to read when deciding whether a follow-up change can
delete `scripts/`. (It cannot.)

### Independent of `scripts/` (real new code)

- `core/paths.py` — pure helpers (`PROJECT_ROOT`, `rel`,
  `resolve_project_path`, `current_timestamp_utc`).
- `core/plot_types.py` — hard-codes the v1.0 supported plot type set.
- `core/report_writer.py` — owns the `report_package` layout,
  `figure_index.md`, and `run_report.json` writer.

### Wraps `scripts/` (façade)

- `core/config_validator.py` — calls
  `validate_origin_plot_config.load_yaml` and
  `validate_origin_plot_config.validate_config`.
- `core/data_loader.py` — calls `origin_plot_from_config.detect_format`
  and `origin_plot_from_config.read_dataframe`.
- `core/style_profiles.py` — calls
  `origin_plot_from_config.load_optional_profile` and
  `effective_export_settings`.

### Shells out to `scripts/`

- `core/origin_executor.py` — spawns
  `python scripts/origin_plot_from_config.py` via `subprocess.run` and
  reads back `reports/origin_plot_v0_2_report.json`.

### Re-exports `scripts/`

- Every Python file under `ops/*` — uses `ops/_runner.py` (which calls
  `runpy.run_path`) to invoke the corresponding `scripts/<name>.py`.

## Why this is acceptable in v1.0

The v0.8.7 implementation is the most heavily exercised part of the
Skill. Replacing it carries risk that v1.0 explicitly did not take on.
The scope of v1.0 was the public surface, the contracts, and the
Codex-handles-data-understanding boundary. That work is done.

If `scripts/origin_plot_from_config.py` were deleted today,
`core/data_loader.py`, `core/style_profiles.py`,
`core/config_validator.py`, and `core/origin_executor.py` all break. The
Origin control logic has not moved.

## What full internalization (v1.1+) would mean

A future v1.1+ may, when there is justification:

- Move the validation, data loading, style profile loading, and Origin
  execution implementations into `core/` as native modules.
- Replace every `ops/*` runpy shim with a real module.
- Physically move the legacy `scripts/` into
  `archive/v0_8_7_full_stack/scripts/` and remove the originals from the
  live tree.
- Drop `core/_legacy.py` and the `subprocess.run` trampoline in
  `core/origin_executor.py`.

That work is **not in v1.0 scope and is not scheduled in this plan.** It
should land only after v1.0 has demonstrated stability against real
usage for at least one cycle.

## Cross-links

- `archive/v0_8_7_full_stack/README.md` — the v0.8.7 frozen surface that
  v1.0 keeps verbatim.
- `contracts/non_goals.md` — what `origin-plot` will and will not absorb.
- `archive/v0_9_smart_input_reference.md` — the smart-input experiment
  that lives outside v1.0 by design.
