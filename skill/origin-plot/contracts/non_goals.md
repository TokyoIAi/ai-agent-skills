# origin-plot non-goals (v1.0)

`origin-plot` is a stable Origin / OriginPro plot execution backend. It
receives a canonical data file and a plot config and produces PNG / PDF /
OPJU. It does **not** infer; it executes explicit canonical config.

This document is the wall against scope creep. Use it as a citation when a
request would push `origin-plot` outside its mandate.

## A. Hard non-goals

These will never enter `origin-plot`. They are routed to **Codex** or to a
**sibling Skill** (`skill/codex-data-wrangler/` or
`skill/origin-plot-smart/`). They never become flags, sub-modes, or
experimental folders inside `origin-plot`.

- **OCR.** Image / scanned-document text extraction. Belongs to the data
  understanding layer (Codex). See
  `contracts/canonical_data_contract.md`.
- **Handwriting recognition.** Same rationale.
- **Image / photo / screenshot data extraction.** Photos of lab notebooks
  or screenshots of tables are not canonical inputs.
- **Smart column-role inference.** `origin-plot` never guesses which
  column is X / Y / error / group. The plot config must name them
  explicitly. See `contracts/plot_config_schema.md`.
- **Automatic graph-type recommendation.** `origin-plot` never picks
  `graph_type` based on data shape. The config sets it.
- **Excel sheet auto-detection.** When `input_format: xlsx`, the config
  must supply `sheet_name` (string or int) or accept the documented
  default. No "look at all sheets and pick the best one".
- **Excel header-row auto-detection.** The first non-empty row is the
  header. No "scan for the row that looks most like headers".
- **Guessing user intent.** Any request that requires the Skill to infer
  what the user "probably" wants is out of scope.

The escalation rule for hard non-goals is unconditional: **route to Codex
or to a sibling Skill, never add the capability to `origin-plot`.**

## B. Not in v1.0 scope, but possible future backend features

These features **may** land in a future v1.x version of `origin-plot`
**only** when the request arrives with a canonical config that already
encodes the user's intent. Each item below has a strict gating contract.
The Skill never infers; it executes.

### Grouped plotting

Grouped plotting may land only when one of the two following canonical
contracts is satisfied. There is no third "convenience" path.

**Contract A — wide-form data:**

The canonical CSV / XLSX is already pivoted into wide form. The config
supplies:

- `x_column` — explicit, single column name.
- `y_columns` — explicit list, every series named.
- `graph_type` — explicit (`line`, `line_symbol`, or `scatter`).

The Skill plots one series per `y_column` and never pivots, never infers
which columns are series, and never derives a group identifier. There is
no `group_column` field in this contract.

**Contract B — long-form data:**

The canonical CSV / XLSX is in long form (one row per observation, with a
group label column). The config supplies all four fields explicitly:

- `x_column` — explicit, single column name.
- `value_column` — explicit, single column name (the numeric value to
  plot).
- `group_column` — explicit, single column name (the group label).
- `graph_type` — explicit (`grouped_line` or `grouped_scatter`).

The Skill performs a deterministic pivot using exactly the names given.
The Skill never infers `value_column`, never infers `group_column`, and
never picks `graph_type` automatically. Ambiguous input (missing field,
non-numeric value column, multiple plausible group columns) is rejected
with a clear validation error.

### Multi-panel plotting

Only with an explicit `panels` list in the config. Each panel names its
own `x_column`, `y_columns`, and panel index. No automatic panel splitting
from a category column. No "smart layout".

### Faceted plotting

Only as a special case of Contract B (long-form grouped) plus an explicit
`facet_column`. The Skill never infers the faceting dimension.

### Origin template reuse

Only with an explicit template path and an explicit mapping from
worksheet columns to template plot designations. No automatic template
discovery, no "find a matching template" heuristic.

### OPJU / OTPU template-based execution

Same gating as Origin template reuse: deterministic template path,
explicit column mapping, no discovery.

## Operational rule

- **Tier A (hard non-goals).** Never. Routed to Codex or to a sibling
  Skill. They never become flags, sub-modes, or experimental folders
  inside `origin-plot`.
- **Tier B.** May land in a future v1.x version of `origin-plot` **only**
  when the request arrives with a canonical config that already encodes
  the user's intent. Until then, the same routing rule as tier A applies.

The closing principle is non-negotiable:

> **origin-plot never infers; it executes explicit canonical config.**

## Cross-links

- `archive/v0_9_smart_input_reference.md` — v0.9 smart-input experiment
  and where it lives now.
- `archive/v1_0_scope_clarification.md` — what v1.0-core-refactor
  actually changed.
- `contracts/codex_data_wrangler_contract.md` — Codex's responsibility
  for data understanding upstream of `origin-plot`.
- `contracts/canonical_data_contract.md` — what canonical input data
  looks like.
- `contracts/plot_config_schema.md` — the explicit fields the plot config
  must supply.
