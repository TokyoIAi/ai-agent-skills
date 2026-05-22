# origin-plot directory map

A 60-second tour. For each top-level directory: what it holds, who uses
it, when to start there.

## Top-level tree

```
skill/origin-plot/
├── README.md                      # start here
├── DIRECTORY.md                   # you are here
├── AGENT_USAGE.md                 # shared agent guide (v1.0.3)
├── CODEX.md                       # Codex-specific operating guide (v1.0.3)
├── CLAUDE.md                      # Claude-specific operating guide (v1.0.3)
├── AGENT_ONBOARDING_TEST.md       # 60-second comprehension test (v1.0.3)
├── requirements.txt               # Python deps for the v0.8.7 backend
│
├── core/                          # v1.0 Python façade over scripts/
├── workflows/                     # daily entry CLIs (run_plot, run_batch, ...)
├── contracts/                     # Codex contract layer (read-only docs)
├── configs/                       # plot configs + reusable profiles
│   ├── examples/                  # shipped worked examples
│   ├── fitting/                   # fitting configs
│   ├── errorbar/                  # errorbar configs
│   ├── batch/                     # batch configs
│   ├── styles/                    # style profiles
│   ├── exports/                   # export profiles
│   ├── sessions/                  # session profiles
│   ├── scan/                      # directory-scan configs
│   └── generated/                 # generated configs (Codex writes here)
├── data/
│   ├── raw/                       # Codex stages messy upstream input here
│   ├── cleaned/                   # Codex writes canonical CSV/XLSX here
│   ├── examples/                  # canonical datasets used by examples
│   └── batch_inputs/              # canonical inputs used by batch examples
├── scripts/                       # v0.8.7 verified implementation (source of truth)
├── ops/                           # advanced maintenance tooling
│   ├── diagnostics/
│   ├── health/
│   ├── hygiene/
│   ├── release/
│   ├── reports/
│   └── smoke/
├── archive/                       # historical documentation anchors
│   ├── README.md
│   ├── v0_8_7_full_stack/         # anchor for the v0.8.7 backend in scripts/
│   ├── v0_9_smart_input_reference.md
│   └── v1_0_scope_clarification.md
├── reports/
│   └── report_package/            # primary deliverable after every run
├── reports_or_notes/              # human-readable notes and simulations (v1.0.3)
│   └── agent_onboarding_simulation.md
├── output/                        # generated exports (NEVER commit)
└── .agents/skills/origin-plot/SKILL.md   # the Skill metadata file
```

## Where to start

| Audience | Start here |
|---|---|
| Daily users (just plot something) | [`skill/origin-plot/workflows/README.md`](workflows/README.md) |
| Codex / Claude (handle messy data and emit canonical CSV + YAML) | [`skill/origin-plot/contracts/README.md`](contracts/README.md) |
| Fresh agent (any role) onboarding | [`skill/origin-plot/AGENT_USAGE.md`](AGENT_USAGE.md), then [`skill/origin-plot/CODEX.md`](CODEX.md) or [`skill/origin-plot/CLAUDE.md`](CLAUDE.md), then [`skill/origin-plot/AGENT_ONBOARDING_TEST.md`](AGENT_ONBOARDING_TEST.md) |
| Advanced maintainers (smoke tests, health, hygiene, release) | [`skill/origin-plot/ops/README.md`](ops/README.md) |
| Historians (why things are where they are) | [`skill/origin-plot/archive/README.md`](archive/README.md) |

**Do not start from `scripts/`** unless you are debugging the legacy
backend. The v0.8.7 implementation under `scripts/` is the source of
truth for Origin control, but it is *not* the documented entry surface.
The documented entry surface is `workflows/`.

## What each top-level directory is for

### `core/`

Thin Python layer that wraps the verified v0.8.7 backend.

- `core/paths.py`, `core/plot_types.py`, `core/report_writer.py` are real
  new code.
- `core/config_validator.py`, `core/data_loader.py`,
  `core/style_profiles.py` are wrappers around `scripts/...`.
- `core/origin_executor.py` shells out to
  `scripts/origin_plot_from_config.py`.

This is a v1.0 **façade**, not a re-implementation. See
[`skill/origin-plot/archive/v1_0_scope_clarification.md`](archive/v1_0_scope_clarification.md).

### `workflows/`

Public CLIs. This is where daily users start.

- `run_plot.py` — render a single plot from a YAML config.
- `run_batch.py` — render multiple plots from a batch YAML.
- `accept_core.py` — minimal acceptance suite (3 examples + path leak scan).
- `build_report_package.py` — rebuild `reports/report_package/` from a
  legacy single-plot report.

See [`skill/origin-plot/workflows/README.md`](workflows/README.md).

### `contracts/`

Read-only documentation that defines the Codex ↔ origin-plot boundary.

- `canonical_data_contract.md` — what canonical CSV / XLSX looks like.
- `plot_config_schema.md` — required and optional fields in the plot YAML.
- `codex_data_wrangler_contract.md` — what Codex must do upstream.
- `non_goals.md` — hard non-goals + tier-B candidates with gating rules.

See [`skill/origin-plot/contracts/README.md`](contracts/README.md).

### `configs/`

YAML configs. The v1.0 surface lives in `configs/examples/`; the rest of
the directories are inherited from v0.8.7 and are still functional. Any
new generated config from Codex should go in `configs/generated/`.

### `data/`

- `data/raw/` — Codex stages messy upstream input here. Bulky binaries
  may be git-ignored.
- `data/cleaned/` — Codex writes canonical CSV / XLSX here. This is the
  file `input_file:` in the YAML should point at.
- `data/examples/` — canonical datasets used by `configs/examples/`.
- `data/batch_inputs/` — canonical inputs used by the v0.8.7 batch
  examples.

### `scripts/`

The verified v0.8.7 implementation. **Source of truth for Origin
control.** It contains the executor, validator, batch script, retry /
session-health utilities, smoke tests, and hygiene scanner.

The v1.0 façade in `core/` and the re-exports in `ops/` both call into
`scripts/`. Do not edit `scripts/` casually; treat it as frozen until a
v1.x ships native replacements.

### `ops/`

Advanced maintenance tooling — smoke tests, session health, hygiene
scans, release-time guards, cross-report rollups. Each script is a thin
re-export of a `scripts/...` module. None of this is required for daily
plotting.

See [`skill/origin-plot/ops/README.md`](ops/README.md).

### `archive/`

Documentation anchors only. Nothing in `archive/` runs.

- `archive/v0_8_7_full_stack/README.md` explains why the v0.8.7 source
  still lives in `scripts/` instead of being physically moved.
- `archive/v0_9_smart_input_reference.md` records where the v0.9
  smart-input experiment lives now (immutable tag plus archive branch)
  and how to inspect it without dragging it back into the mainline.
- `archive/v1_0_scope_clarification.md` documents that v1.0 was a
  public surface refactor, not a re-implementation.

See [`skill/origin-plot/archive/README.md`](archive/README.md).

### Top-level agent docs (added in v1.0.3)

The four Markdown files at the root of `skill/origin-plot/` form the
agent onboarding layer:

- [`skill/origin-plot/AGENT_USAGE.md`](AGENT_USAGE.md) — shared agent
  guide. Read first.
- [`skill/origin-plot/CODEX.md`](CODEX.md) — Codex-specific operating
  guide.
- [`skill/origin-plot/CLAUDE.md`](CLAUDE.md) — Claude-specific operating
  guide.
- [`skill/origin-plot/AGENT_ONBOARDING_TEST.md`](AGENT_ONBOARDING_TEST.md)
  — 60-second comprehension test.

These files are documentation only. They do not change behaviour, do not
ship code, and do not extend the YAML schema. They tell agents how to
use the existing public surface.

### `reports_or_notes/`

Human-readable notes and worked examples added in v1.0.3.

- [`skill/origin-plot/reports_or_notes/agent_onboarding_simulation.md`](reports_or_notes/agent_onboarding_simulation.md)
  — Claude simulating a fresh agent answering the eight-question
  onboarding test using only the v1.0.3 documentation.

This directory is for documentation artifacts. It is **not** the
deliverable directory; the deliverable lives in
[`skill/origin-plot/reports/report_package/`](reports/report_package/).

### `reports/`

Generated reports. The committable subset is documented in
[`skill/origin-plot/README.md`](README.md) and the path leak scanner
enforces the rule about absolute paths. `reports/report_package/` is the
primary deliverable for every workflow run.

### `output/`

Raw Origin exports. **Always git-ignored. Never commit.**

## Why v0.9 smart-input is not visible here

v0.9 added a smart input layer (`analyze_data_source.py`,
`run_smart_plot.py`, `data/smart_inputs/`, etc.) that did data
understanding inside `origin-plot`. v1.0 reverted that direction. The
v0.9 work is preserved by:

- the immutable tag `v0.9-origin-plot-smart-input` (commit `7c67545`)
- the frozen archive branch `archive/skill-v0.9-smart-input`

Inspect read-only via:

```
git show v0.9-origin-plot-smart-input:skill/origin-plot/scripts/analyze_data_source.py
git worktree add ../origin-plot-v0.9-view v0.9-origin-plot-smart-input
```

Do not `git checkout` v0.9 paths into the v1.0 working tree. See
[`skill/origin-plot/archive/v0_9_smart_input_reference.md`](archive/v0_9_smart_input_reference.md).

## Layering reminder

- The **agent docs** at the root of `skill/origin-plot/`
  ([`AGENT_USAGE.md`](AGENT_USAGE.md), [`CODEX.md`](CODEX.md),
  [`CLAUDE.md`](CLAUDE.md), [`AGENT_ONBOARDING_TEST.md`](AGENT_ONBOARDING_TEST.md))
  are for **onboarding**. They explain the boundary, the standard
  workflow, and the never-do list. They do not redefine the contract.
- The **canonical contract** lives in
  [`skill/origin-plot/contracts/`](contracts/README.md). When the
  agent docs and the contracts disagree about a schema field, the
  contracts win. Schema changes only happen with an explicit contract
  revision.
- The **daily entry surface** is
  [`skill/origin-plot/workflows/`](workflows/README.md). Agents call
  `workflows\run_plot.py` and `workflows\run_batch.py`, never
  `scripts/origin_plot_from_config.py` directly.
- [`skill/origin-plot/scripts/`](scripts/) is the **legacy** verified
  implementation and is the source of truth for Origin control. Treat
  it as frozen unless you are debugging a v0.8.x backend issue.
