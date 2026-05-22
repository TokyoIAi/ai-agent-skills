# archive/

Documentation anchors for the historical layers of `origin-plot`.

Nothing in `archive/` runs. This directory holds **only** documents that
explain why the live tree looks the way it does and where past
experiments live now.

## Files

| Path | Purpose |
|---|---|
| [`v0_8_7_full_stack/README.md`](v0_8_7_full_stack/README.md) | Why the v0.8.7 implementation still lives in [`../scripts/`](../scripts/) instead of being physically moved here. |
| [`v0_9_smart_input_reference.md`](v0_9_smart_input_reference.md) | Where the v0.9 smart-input experiment lives now (immutable tag plus archive branch) and how to inspect it without dragging it back into the v1.0 mainline. |
| [`v1_0_scope_clarification.md`](v1_0_scope_clarification.md) | What `v1.0-core-refactor` actually changed (public surface, contracts) and what it deliberately did not change (`core/` is still a façade over `scripts/`). |

## What is and isn't in archive form

### v0.8.7 — not yet physically archived

The v0.8.7 backend is still the source of truth for Origin control. Its
source code lives at [`../scripts/`](../scripts/), not here.
[`v0_8_7_full_stack/README.md`](v0_8_7_full_stack/README.md) explains
why moving the source to `archive/` would break `core/origin_executor.py`,
the `ops/_runner.py` shims, and the `core/...` wrappers. Physical
archival is a v1.1+ task, not v1.0.

### v0.9 — preserved through tag and frozen branch

The v0.9 smart-input experiment is **not** in the live tree. It is
preserved by:

- the immutable tag `v0.9-origin-plot-smart-input` (commit
  `7c675455dda806130cc65ba19cedccc6c97afff5`);
- the frozen branch `archive/skill-v0.9-smart-input` (same SHA as the
  tag).

The branch is a frozen pointer; never push to it. Read-only inspection:

```
git show v0.9-origin-plot-smart-input:skill/origin-plot/scripts/analyze_data_source.py
git worktree add ../origin-plot-v0.9-view v0.9-origin-plot-smart-input
```

Do **not** use `git checkout v0.9-... -- <path>` to read v0.9; that
modifies the working tree.

### Why v0.9 is not in the v1.0 mainline

Smart input is data understanding. v1.0 is a stable Origin execution
backend. Data understanding belongs to **Codex** or to a sibling Skill,
not inside `origin-plot`. Full reasoning:
[`v0_9_smart_input_reference.md`](v0_9_smart_input_reference.md) and
[`../contracts/non_goals.md`](../contracts/non_goals.md).

## Future smart-input

If real-world demand for smart-input recurs, design it as a **sibling
Skill** under `skill/`, not as a subdirectory of `origin-plot/`:

- `skill/codex-data-wrangler/` — a Codex-style data understanding Skill
  that emits canonical CSV / XLSX plus a v1.0-compatible plot config and
  invokes `workflows/run_plot.py`.
- `skill/origin-plot-smart/` — alternative naming if the smart layer is
  considered tightly coupled to origin-plot's output contract.

This document does not schedule that work. It only records that the
landing place is a sibling Skill, never `skill/origin-plot/`.

## Cross-links

- Live entry surface: [`../workflows/README.md`](../workflows/README.md)
- Codex boundary: [`../contracts/README.md`](../contracts/README.md)
- Hard non-goals: [`../contracts/non_goals.md`](../contracts/non_goals.md)
- Top-level navigation: [`../DIRECTORY.md`](../DIRECTORY.md)
