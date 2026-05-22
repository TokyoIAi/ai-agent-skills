# v0.9 smart-input archive reference

Smart-input was a v0.9 experimental front end that added CSV / XLSX / TSV /
TXT / Markdown auto-analysis, column-role inference, and grouped plotting
on top of `origin-plot`. It is **not** part of v1.0.

The v1.0 `origin-plot` mainline is a stable Origin / OriginPro plot
execution backend. Data understanding (Excel parsing, Markdown extraction,
unit detection, column-role inference, graph-type recommendation) is
**Codex's responsibility** and lives outside `origin-plot`. See
`contracts/codex_data_wrangler_contract.md` and `contracts/non_goals.md`.

## Where v0.9 lives now

- **Immutable tag:** `v0.9-origin-plot-smart-input` at commit
  `7c675455dda806130cc65ba19cedccc6c97afff5`.
- **Archive branch:** `archive/skill-v0.9-smart-input` (frozen pointer; same
  SHA as the tag).

The archive branch is a **frozen pointer**. It must never be the target of
a merge, rebase, force-push, or any push that changes its tip.

## What was in v0.9

Files added under v0.9 that are **not** present on the v1.0 mainline:

- `configs/smart/smart_input_config.yaml`
- `configs/generated/smart_generated_plot_config.yaml`
- `data/smart_inputs/sample_excel_like.csv`
- `data/smart_inputs/sample_errorbar.csv`
- `data/smart_inputs/sample_grouped.csv`
- `data/smart_inputs/sample_markdown_table.md`
- `data/smart_inputs/sample_excel_book.xlsx`
- `data/smart_inputs/_generate_excel_book.py`
- `scripts/analyze_data_source.py`
- `scripts/run_smart_plot.py`
- `scripts/test_smart_input_logic.py`
- `reports/smart_input_analysis_report.json`
- `reports/smart_plot_run_report.json`

Files modified under v0.9 that are **reverted** on the v1.0 mainline (i.e.
the v1.0 versions match the v0.8.7 freeze):

- `scripts/origin_plot_from_config.py` — v0.9 added `grouped_line` /
  `grouped_scatter` pivot path. Not in v1.0.
- `scripts/validate_origin_plot_config.py` — v0.9 added grouped types and
  `group_column` validation. Not in v1.0.
- `scripts/run_smoke_tests.py` — v0.9 registered
  `test_smart_input_logic`. Not in v1.0.

## How to inspect v0.9 read-only

The following commands do **not** modify the v1.0 working tree.

### Read a single file's content

```
git show v0.9-origin-plot-smart-input:skill/origin-plot/scripts/analyze_data_source.py
git show v0.9-origin-plot-smart-input:skill/origin-plot/configs/smart/smart_input_config.yaml
```

`git show <tag>:<path>` writes nothing to disk. It prints the file content
captured by the tag.

### Browse the full v0.9 tree without leaving the v1.0 working tree

Use a separate worktree:

```
git worktree add ../origin-plot-v0.9-view v0.9-origin-plot-smart-input
# inspect at ../origin-plot-v0.9-view/skill/origin-plot/
git worktree remove ../origin-plot-v0.9-view
```

The worktree is an isolated filesystem view; the v1.0 mainline working tree
is untouched.

## What you must not do

- Do **not** use `git checkout v0.9-origin-plot-smart-input -- <path>` to
  "inspect" v0.9. That command modifies the current working tree and will
  reintroduce v0.9 source into the v1.0 mainline. It is not a read-only
  operation.
- Do **not** copy v0.9 files back into `skill/origin-plot/` by any means
  (checkout, copy, cherry-pick, restore, manual edit). The mainline tree
  must remain free of v0.9 source.
- Do **not** push to `archive/skill-v0.9-smart-input`. It is a frozen
  pointer.

## Where smart-input could land in the future

If real-world demand for smart-input recurs, design it as a **sibling
Skill**, not as a folder inside `origin-plot`:

- `skill/codex-data-wrangler/` — a Codex-style data understanding Skill
  that emits canonical CSV / XLSX plus a v1.0-compatible plot config and
  invokes `workflows/run_plot.py`.
- `skill/origin-plot-smart/` — alternative naming if the smart layer is
  considered tightly coupled to origin-plot's output contract.

This document does **not** schedule that work. It only documents that the
landing place is a sibling Skill, never `skill/origin-plot/`.

## Cross-links

- `contracts/non_goals.md` — explicit hard non-goals and tier-B
  conditional features for `origin-plot`.
- `archive/v1_0_scope_clarification.md` — what v1.0-core-refactor actually
  changed and what it deliberately did not change.
- `contracts/codex_data_wrangler_contract.md` — the canonical interface
  between Codex and `origin-plot`.
- [`skill/origin-plot/archive/v0_8_7_full_stack/README.md`](v0_8_7_full_stack/README.md) — documentation anchor for the
  v0.8.7 implementation that v1.0 keeps verbatim under `scripts/`.
