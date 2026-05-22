# Agent onboarding simulation — origin-plot v1.0.3

A worked simulation of a fresh agent (Claude) running the eight-question
onboarding test in
[`skill/origin-plot/AGENT_ONBOARDING_TEST.md`](../AGENT_ONBOARDING_TEST.md).
The agent reads only the v1.0.3 documentation set and answers from that
material; nothing in this document is paraphrased from the actual
Origin source code.

## Setup

The simulated agent has been pointed at:

- [`skill/origin-plot/README.md`](../README.md)
- [`skill/origin-plot/AGENT_USAGE.md`](../AGENT_USAGE.md)
- [`skill/origin-plot/CLAUDE.md`](../CLAUDE.md)
- [`skill/origin-plot/DIRECTORY.md`](../DIRECTORY.md)
- [`skill/origin-plot/contracts/README.md`](../contracts/README.md)
- [`skill/origin-plot/contracts/non_goals.md`](../contracts/non_goals.md)

The agent has not seen any v0.9 file. The agent has not browsed the
`scripts/` source. The agent has 60 seconds.

## Q1. What is `origin-plot`?

**Agent answer.** `origin-plot` is a stable Origin / OriginPro plot
execution backend. It accepts canonical CSV / XLSX / TSV / TXT data plus
an explicit YAML plot config, validates the config, drives Origin
through the verified executor, and emits PNG, PDF, OPJU, and a
[`skill/origin-plot/reports/report_package/`](../reports/report_package/)
bundle.

It is not a data understanding tool. Data wrangling happens upstream.

**Verdict.** PASS. Matches
[`skill/origin-plot/README.md`](../README.md) sections 1 and 3.

## Q2. What is `origin-plot` NOT?

**Agent answer.** It does not do OCR, handwriting recognition, image /
photo / screenshot extraction, smart column-role inference, automatic
graph-type recommendation, Excel sheet auto-detection, Excel
header-row auto-detection, or guessing user intent. Those belong to
Codex or to a sibling Skill, never to `origin-plot`. The full list and
the gating rules for tier-B candidates live in
[`skill/origin-plot/contracts/non_goals.md`](../contracts/non_goals.md).

**Verdict.** PASS. Matches
[`skill/origin-plot/README.md`](../README.md) section 2 and
[`skill/origin-plot/contracts/non_goals.md`](../contracts/non_goals.md).

## Q3. What is the daily entry command?

**Agent answer.** Run from `skill/origin-plot/`:

```powershell
py workflows\run_plot.py --config configs\examples\line_plot.yaml
```

For multi-job batches:

```powershell
py workflows\run_batch.py --batch-config configs\examples\batch.yaml
```

For the minimal acceptance suite:

```powershell
py workflows\accept_core.py
```

A passing acceptance run ends with `PASS: origin-plot core acceptance ok`.

**Verdict.** PASS. Matches
[`skill/origin-plot/README.md`](../README.md) section 4 and
[`skill/origin-plot/workflows/README.md`](../workflows/README.md).

## Q4. Where do canonical data and config go before invoking the workflow?

**Agent answer.**

- Canonical data: write the cleaned CSV / XLSX to
  [`skill/origin-plot/data/cleaned/<dataset>.csv`](../data/cleaned/).
  Stage messy upstream artifacts under
  [`skill/origin-plot/data/raw/`](../data/raw/) only.
- Plot config: write the YAML to
  [`skill/origin-plot/configs/generated/<dataset>.yaml`](../configs/generated/)
  (or use one of the worked configs in
  [`skill/origin-plot/configs/examples/`](../configs/examples/)).
- Profiles: reference style and export profiles from
  [`skill/origin-plot/configs/styles/`](../configs/styles/) and
  [`skill/origin-plot/configs/exports/`](../configs/exports/).

The YAML must list `x_column`, `y_columns`, and `graph_type`
explicitly. The workflow does not infer them.

**Verdict.** PASS. Matches
[`skill/origin-plot/README.md`](../README.md) section 5 and
[`skill/origin-plot/contracts/README.md`](../contracts/README.md).

## Q5. Where is the deliverable after a successful run?

**Agent answer.**
[`skill/origin-plot/reports/report_package/`](../reports/report_package/).
After a passing run it contains:

```
reports/report_package/
  figures/<basename>.png
  figures/<basename>.pdf
  origin_projects/<basename>.opju
  configs/<config>.yaml
  figure_index.md
  run_report.json
```

`figure_index.md` is the human-readable index;
`run_report.json` is the machine-readable summary. The raw exports the
executor produces live under
[`skill/origin-plot/output/`](../output/), which is git-ignored and
must never be committed.

**Verdict.** PASS. Matches
[`skill/origin-plot/README.md`](../README.md) section 6.

## Q6. Why is v0.9 smart-input not in the v1.0 mainline?

**Agent answer.** Smart-input was a v0.9 experiment that put data
understanding inside `origin-plot`. v1.0 reverted that direction
because data understanding belongs to Codex (or a sibling Skill), not
to a stable execution backend. v0.9 is preserved by:

- the immutable tag `v0.9-origin-plot-smart-input` (commit
  `7c67545`);
- the frozen branch `archive/skill-v0.9-smart-input`, which is a
  pointer at the same commit and is never pushed forward.

Read-only inspection uses
`git show v0.9-origin-plot-smart-input:<path>` or
`git worktree add ../origin-plot-v0.9-view v0.9-origin-plot-smart-input`.
Never `git checkout v0.9-... -- <path>`; that overwrites the v1.0
working tree. See
[`skill/origin-plot/archive/v0_9_smart_input_reference.md`](../archive/v0_9_smart_input_reference.md).

**Verdict.** PASS. Matches
[`skill/origin-plot/archive/v0_9_smart_input_reference.md`](../archive/v0_9_smart_input_reference.md)
and the v0.9-related entries in
[`skill/origin-plot/DIRECTORY.md`](../DIRECTORY.md).

## Q7. What is `core/` and what does it actually contain?

**Agent answer.**
[`skill/origin-plot/core/`](../core/) is the v1.0 Python façade over
the verified v0.8.7 backend that still lives in
[`skill/origin-plot/scripts/`](../scripts/). It is not a
re-implementation.

- `core/paths.py`, `core/plot_types.py`, `core/report_writer.py` are
  the only pieces of new v1.0 code.
- `core/config_validator.py`, `core/data_loader.py`, and
  `core/style_profiles.py` are wrappers around matching `scripts/...`
  modules.
- `core/origin_executor.py` shells out to
  `scripts/origin_plot_from_config.py`. Source of truth for Origin
  control remains in `scripts/`.

Full internalization is a v1.1+ task. See
[`skill/origin-plot/archive/v1_0_scope_clarification.md`](../archive/v1_0_scope_clarification.md).

**Verdict.** PASS. Matches
[`skill/origin-plot/archive/v1_0_scope_clarification.md`](../archive/v1_0_scope_clarification.md)
and the description of `core/` in
[`skill/origin-plot/DIRECTORY.md`](../DIRECTORY.md).

## Q8. What must NOT happen in any commit on the `skill` branch?

**Agent answer.**

- Do not commit
  [`skill/origin-plot/output/`](../output/) — git-ignored, generated.
- Do not commit reports with absolute local paths (`H:\`, `C:\`,
  `E:\`, `/mnt/`); the path leak scanner
  [`skill/origin-plot/scripts/check_committed_reports.py`](../scripts/check_committed_reports.py)
  enforces this.
- Do not modify Origin control logic. The v0.8.7 backend in
  [`skill/origin-plot/scripts/`](../scripts/) and the v1.0 façade in
  [`skill/origin-plot/core/`](../core/) and the v1.0 CLIs in
  [`skill/origin-plot/workflows/`](../workflows/) are frozen for a
  doc-only patch.
- Do not introduce GUI automation (`pyautogui`, screenshot
  recognition, mouse-coordinate clicks, auto-clicking Origin dialogs).
- Do not reintroduce v0.9 smart-input. Future smart-input work goes
  to a sibling Skill, never inside
  [`skill/origin-plot/`](../).

**Verdict.** PASS. Matches the hard rules in
[`skill/origin-plot/README.md`](../README.md),
[`skill/origin-plot/AGENT_USAGE.md`](../AGENT_USAGE.md), and the
do-not-do list in
[`skill/origin-plot/CLAUDE.md`](../CLAUDE.md).

## Overall

8 / 8 PASS. No fabricated capabilities. No bare `README.md` references;
every cited path is full (`skill/origin-plot/...`). The simulation
shows the v1.0.3 documentation set is sufficient for an agent to clear
the comprehension test in under 60 seconds.

## See also

- [`skill/origin-plot/AGENT_ONBOARDING_TEST.md`](../AGENT_ONBOARDING_TEST.md)
  — the test procedure and expected answers.
- [`skill/origin-plot/AGENT_USAGE.md`](../AGENT_USAGE.md) — the shared
  agent guide that the simulated agent read first.
- [`skill/origin-plot/CLAUDE.md`](../CLAUDE.md) — Claude's
  role-specific guide.
- [`skill/origin-plot/CODEX.md`](../CODEX.md) — Codex's role-specific
  guide.
