# AGENT_ONBOARDING_TEST — origin-plot

A 60-second comprehension test for any agent (Codex, Claude, or other
LLM-driven assistant) before they take real work on `origin-plot`. The
agent must be able to answer all eight questions correctly, using only
the docs, in under 60 seconds. If they cannot, they have not finished
onboarding.

A worked example of an agent answering this test is in
[`skill/origin-plot/reports_or_notes/agent_onboarding_simulation.md`](reports_or_notes/agent_onboarding_simulation.md).

## Test procedure

1. Give the agent the documentation entry point:
   [`skill/origin-plot/README.md`](README.md).
2. Allow them to read any of the following before answering:
   - [`skill/origin-plot/AGENT_USAGE.md`](AGENT_USAGE.md)
   - [`skill/origin-plot/CODEX.md`](CODEX.md) (Codex only)
   - [`skill/origin-plot/CLAUDE.md`](CLAUDE.md) (Claude only)
   - [`skill/origin-plot/DIRECTORY.md`](DIRECTORY.md)
   - [`skill/origin-plot/contracts/README.md`](contracts/README.md)
   - [`skill/origin-plot/contracts/non_goals.md`](contracts/non_goals.md)
3. Ask the eight questions below in order. The agent answers from
   memory or by quoting full repository-relative paths.
4. Mark each answer pass / fail against the expected answer.
5. Pass condition: **all eight answers correct**, no fabricated
   capabilities, no bare `README.md` references.

## Questions and expected answers

### Q1. What is `origin-plot`?

**Expected:** A stable Origin / OriginPro plot execution backend. It
takes canonical CSV / XLSX / TSV / TXT data plus an explicit YAML plot
config and exports PNG / PDF / OPJU plus a `report_package/` bundle. It
does not do data understanding.

### Q2. What is `origin-plot` NOT?

**Expected:** It does not do OCR, handwriting recognition, image /
photo / screenshot data extraction, smart column-role inference,
automatic graph-type recommendation, Excel sheet / header
auto-detection, or guessing user intent. The full list lives in
[`skill/origin-plot/contracts/non_goals.md`](contracts/non_goals.md).

### Q3. What is the daily entry command?

**Expected:**

```powershell
py workflows\run_plot.py --config configs\examples\line_plot.yaml
```

Run from `skill/origin-plot/`. For batches, use
`py workflows\run_batch.py --batch-config <batch.yaml>`. For the
self-check, use `py workflows\accept_core.py`.

### Q4. Where do canonical data and config go before invoking the workflow?

**Expected:**

- Canonical data:
  [`skill/origin-plot/data/cleaned/<dataset>.csv`](data/cleaned/) (or
  `.xlsx`).
- Plot config:
  [`skill/origin-plot/configs/generated/<dataset>.yaml`](configs/generated/).
- Worked examples live in
  [`skill/origin-plot/configs/examples/`](configs/examples/) and
  [`skill/origin-plot/data/examples/`](data/examples/).

### Q5. Where is the deliverable after a successful run?

**Expected:**
[`skill/origin-plot/reports/report_package/`](reports/report_package/),
containing `figures/<basename>.png`, `figures/<basename>.pdf`,
`origin_projects/<basename>.opju`, `figure_index.md`, and
`run_report.json`.

### Q6. Why is v0.9 smart-input not in the v1.0 mainline?

**Expected:** Smart-input is data understanding. v1.0 is a stable
Origin execution backend. Data understanding belongs to Codex or to a
sibling Skill, not to `origin-plot`. v0.9 is preserved by the immutable
tag `v0.9-origin-plot-smart-input` (commit `7c67545`) and the frozen
branch `archive/skill-v0.9-smart-input`. See
[`skill/origin-plot/archive/v0_9_smart_input_reference.md`](archive/v0_9_smart_input_reference.md).

### Q7. What is `core/` and what does it actually contain?

**Expected:**
[`skill/origin-plot/core/`](core/) is the v1.0 Python façade over the
verified v0.8.7 backend in
[`skill/origin-plot/scripts/`](scripts/). It is **not** a
re-implementation. `core/origin_executor.py` shells out to
`scripts/origin_plot_from_config.py`. `core/config_validator.py`,
`core/data_loader.py`, and `core/style_profiles.py` are wrappers around
matching `scripts/...` modules. Full internalization belongs to v1.1+.
See
[`skill/origin-plot/archive/v1_0_scope_clarification.md`](archive/v1_0_scope_clarification.md).

### Q8. What must NOT happen in any commit on the `skill` branch?

**Expected:**

- Do not commit
  [`skill/origin-plot/output/`](output/) (git-ignored, generated).
- Do not commit reports containing absolute local paths (`H:\`, `C:\`,
  `E:\`, `/mnt/`); the path leak scanner
  [`skill/origin-plot/scripts/check_committed_reports.py`](scripts/check_committed_reports.py)
  enforces this.
- Do not modify code under
  [`skill/origin-plot/scripts/`](scripts/) or
  [`skill/origin-plot/core/`](core/) or the
  [`skill/origin-plot/workflows/`](workflows/) Python files when the
  task is doc-only.
- Do not introduce GUI automation (`pyautogui`, screenshot recognition,
  mouse clicks).
- Do not reintroduce v0.9 smart-input under
  [`skill/origin-plot/`](.).

## Pass condition

All eight answers correct, every cited path full
(`skill/origin-plot/...`), and no fabricated capabilities. If any
answer drifts toward "origin-plot can also do OCR / column inference /
sheet detection / smart graph recommendation", the agent has failed and
must reread
[`skill/origin-plot/AGENT_USAGE.md`](AGENT_USAGE.md) before retrying.

## See also

- [`skill/origin-plot/reports_or_notes/agent_onboarding_simulation.md`](reports_or_notes/agent_onboarding_simulation.md)
  — a worked simulation of an agent answering this test using only the
  v1.0.3 documentation.
