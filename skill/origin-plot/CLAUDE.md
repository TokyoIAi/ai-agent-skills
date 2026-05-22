# CLAUDE — origin-plot operating guide

Operating guide for Claude when working on `origin-plot`. Optimised for
planning, boundaries, and not over-engineering. Read
[`skill/origin-plot/AGENT_USAGE.md`](AGENT_USAGE.md) first for the
shared boundary; this document only covers Claude specifics.

## 1. High-level posture

You are a planner with a sharp boundary. The shape of every task is:

1. Understand what the user actually wants from the messy artifact.
2. Confirm whether the task is in scope for `origin-plot` or for an
   upstream / sibling Skill.
3. Write the **canonical** CSV / XLSX and the **explicit** YAML, exactly
   the way [`skill/origin-plot/contracts/`](contracts/README.md) defines
   them.
4. Run the workflow, verify the deliverable, return a tight final
   report.

If a step is ambiguous, **stop and ask**. Do not improvise behavior on
top of `origin-plot`.

## 2. Do-not-expand-scope list

- Do **not** add image / PDF / OCR / handwriting capabilities to
  `origin-plot`. They belong to a sibling Skill.
- Do **not** invent a "smart" mode that infers columns or graph type.
  That regresses to v0.9 and was deliberately excluded from v1.0.
- Do **not** edit anything under
  [`skill/origin-plot/scripts/`](scripts/),
  [`skill/origin-plot/core/`](core/), or the
  [`skill/origin-plot/workflows/`](workflows/) Python files when
  satisfying a user request. They are frozen at v0.8.7 / v1.0.1.
- Do **not** change the YAML schema as a side-effect of a single
  request. Schema changes require a new contract revision.
- Do **not** silently widen a config to handle "what the user probably
  meant". Ask the user first.
- Do **not** remove or relax the path leak scanner. Reports must remain
  free of `H:\`, `C:\`, `E:\`, `/mnt/`.
- Do **not** fall back to GUI clicks. No `pyautogui`, no screenshot
  recognition, no mouse-coordinate automation, no auto-clicking Origin
  dialogs.
- Do **not** reintroduce `data/smart_inputs/` or any
  `analyze_data_source.py` helpers from the v0.9 line.

## 3. Command reference

Run every command from `skill/origin-plot/`.

```powershell
# render a single plot
py workflows\run_plot.py --config configs\examples\line_plot.yaml

# render a batch
py workflows\run_batch.py --batch-config configs\examples\batch.yaml

# fast self-check (3 example configs + path leak scan)
py workflows\accept_core.py

# rebuild reports/report_package/ from an existing legacy report
py workflows\build_report_package.py

# committed-report path leak scan (call before staging changes in reports/)
py scripts\check_committed_reports.py

# Origin process cleanup when retries do not converge
Get-Process Origin64 -ErrorAction SilentlyContinue | Stop-Process -Force
```

The acceptance success line is `PASS: origin-plot core acceptance ok`.

## 4. File-type handling rules

These rules govern **upstream cleaning** before `run_plot.py` is
invoked. They are not implemented inside `origin-plot`.

### 4.1 Excel (`.xlsx`)

- List sheets explicitly and pick one. Do not default silently.
- Set the header row explicitly (row index `header=`). Do not
  auto-search.
- Coerce numeric columns with `pd.to_numeric(..., errors="raise")` so
  that bad cells fail loudly.
- Persist the cleaned subset as UTF-8 CSV to
  `skill/origin-plot/data/cleaned/<dataset>.csv` so the YAML can use
  `input_format: "csv"`. Reading XLSX directly is allowed but CSV
  removes one source of ambiguity.

### 4.2 Markdown / mixed text

- Treat Markdown tables as raw input only. Parse them with a
  deterministic library (or extract the table block manually) and
  produce a clean CSV. Do not feed `origin-plot` a Markdown file.
- Discard prose; canonical data is numeric only (plus optional group
  labels).

### 4.3 Image / photo / screenshot / PDF

- **Out of scope.** `origin-plot` does not do OCR or image extraction.
  See
  [`skill/origin-plot/contracts/non_goals.md`](contracts/non_goals.md).
- Surface the limitation to the user and recommend a sibling Skill that
  emits canonical CSV. Do not attempt to bolt OCR onto `origin-plot`.
- If the user insists, stop. Ask explicitly whether they want to use a
  different Skill or transcribe the data manually. Do not improvise.

### 4.4 Lab notebook / freeform notes

- Treat as upstream input only. Extract numeric records into a clean
  CSV, drop everything else, and proceed with the standard YAML.

### 4.5 Already-canonical CSV / TSV / TXT

- Verify UTF-8, header row at row 1, numeric coercion clean. Then write
  the YAML directly.

## 5. When to stop and ask

Stop and ask before invoking the workflow when any of these are true:

- The Excel file has multiple sheets and the user has not named one.
- The header row is not at row 1.
- Two candidate columns could be `x_column`; both are plausible.
- The graph type is not specified and the data does not unambiguously
  imply one.
- The data has missing values you would otherwise drop or impute.
- The data appears to require grouping (long-form with a group key) but
  the user did not provide explicit `group_column` semantics. Tier B
  grouped plotting requires explicit canonical contract; see
  [`skill/origin-plot/contracts/non_goals.md`](contracts/non_goals.md).
- The request mentions OCR, screenshots, or image extraction. Do not
  attempt; redirect to a sibling Skill.

## 6. Final report format

Use this exact structure for the final reply. Use full
repository-relative paths.

```
status: PASS | PASS with warnings | PASS with session_retry | FAIL
config: skill/origin-plot/configs/generated/<dataset>.yaml
data: skill/origin-plot/data/cleaned/<dataset>.csv
outputs:
  png: skill/origin-plot/reports/report_package/figures/<basename>.png
  pdf: skill/origin-plot/reports/report_package/figures/<basename>.pdf
  opju: skill/origin-plot/reports/report_package/origin_projects/<basename>.opju
report: skill/origin-plot/reports/report_package/run_report.json
hygiene: PASS  (skill/origin-plot/scripts/check_committed_reports.py)
warnings: <list or "none">
notes: <2 short lines maximum>
```

Avoid prose summaries longer than two lines. Avoid promising the user
that any GUI step happened (none did). Do not include screenshots; cite
files instead.

## 7. Cross-links

- Shared boundary:
  [`skill/origin-plot/AGENT_USAGE.md`](AGENT_USAGE.md).
- Codex guide:
  [`skill/origin-plot/CODEX.md`](CODEX.md).
- Daily entry surface:
  [`skill/origin-plot/workflows/README.md`](workflows/README.md).
- Codex contract:
  [`skill/origin-plot/contracts/README.md`](contracts/README.md),
  [`skill/origin-plot/contracts/codex_data_wrangler_contract.md`](contracts/codex_data_wrangler_contract.md).
- Hard non-goals:
  [`skill/origin-plot/contracts/non_goals.md`](contracts/non_goals.md).
- Onboarding test:
  [`skill/origin-plot/AGENT_ONBOARDING_TEST.md`](AGENT_ONBOARDING_TEST.md).
- v1.0 scope clarification:
  [`skill/origin-plot/archive/v1_0_scope_clarification.md`](archive/v1_0_scope_clarification.md).
- v0.9 archive:
  [`skill/origin-plot/archive/v0_9_smart_input_reference.md`](archive/v0_9_smart_input_reference.md).
