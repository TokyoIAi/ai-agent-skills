---
name: origin-plot
description: Use this skill when the task involves generating scientific plots with Origin or OriginPro from CSV/Excel data using Windows Python and the originpro package. Do not use GUI clicking, pyautogui, screenshot recognition, or mouse-coordinate automation.
---

# Origin Plot

## Purpose

Use Windows Python and OriginLab's `originpro` package to generate verified scientific plots in installed Windows Origin/OriginPro from CSV or Excel data. Prefer direct API automation through Origin Automation Server / COM rather than any GUI interaction.

## When to Use

Use this skill for Origin/OriginPro plotting, Origin project generation, batch scientific plots, publication figures, and reproducible CSV/Excel-to-Origin workflows. Use the bundled scripts as templates and adapt them to project data and chart requirements.

## Hard Rules

- Do not use pyautogui.
- Do not use screenshot recognition.
- Do not use mouse-coordinate automation.
- Do not blindly operate the Origin GUI.
- Prefer originpro API.
- Use Windows Python for controlling installed Windows Origin.
- Do not claim success unless output files are actually generated and verified.
- Do not modify Origin installation files, registry entries, or system settings during diagnostics.

## Environment Requirements

- Windows with desktop Origin or OriginPro installed, preferably Origin 2021 or later.
- Windows Python, not WSL Python, for COM-based Origin automation.
- Python packages: `originpro`, `pandas`, and `openpyxl`.
- A readable CSV or Excel input file with at least two numeric columns.
- Write access to the project `output/` directory.

## Expected Project Structure

```text
.agents/skills/origin-plot/
  SKILL.md
  scripts/
    check_origin_env.py
    plot_origin_template.py
  references/
    originpro_usage_notes.md
  assets/
    sample.csv
data/
  sample.csv
output/
  origin_env_report.json
  origin_plot/
```

## Standard Workflow

1. Inspect `data/` for CSV or Excel input files.
2. Run `py .agents\skills\origin-plot\scripts\check_origin_env.py`.
3. Load CSV/Excel data with pandas.
4. Create an Origin worksheet.
5. Send the dataframe to the worksheet.
6. Use the first numeric column as X by default.
7. Use remaining numeric columns as Y by default.
8. Create a line or scatter plot with the `originpro` API.
9. Set title, axis labels, and legend.
10. Rescale the graph layer.
11. Export PNG and PDF.
12. Save the Origin project as OPJU.
13. Verify output files exist before reporting success.

## Data Assumptions

- Default input is `data/sample.csv`; if missing, use `.agents/skills/origin-plot/assets/sample.csv`.
- CSV data should include headers.
- Excel input should be read with pandas and `openpyxl`.
- Numeric columns are selected with pandas dtype inspection.
- At least two numeric columns are required: one X column and one or more Y columns.

## Plotting Defaults

- Plot type: line plot unless the user asks for scatter or another style.
- X axis: first numeric column.
- Y series: all remaining numeric columns.
- Title: derived from the input filename unless the user specifies one.
- Axis labels: use source column names.
- Legend: use Y column names.
- Output directory: `output/origin_plot/`.

## Validation Commands

```powershell
py .agents\skills\origin-plot\scripts\check_origin_env.py
py .agents\skills\origin-plot\scripts\plot_origin_template.py
```

If `py` is unavailable, try the same commands with the Windows `python` executable. Do not use WSL Python to control Windows Origin.

## Acceptance Criteria

- Environment report generated.
- Script runs or reports missing prerequisite truthfully.
- Output PNG exists when Origin environment is available.
- Output PDF exists when Origin environment is available.
- Output OPJU exists when Origin environment is available.
- No GUI clicking automation used.

## Failure Handling

- If `originpro` is missing, report the import failure and suggest `py -m pip install originpro pandas openpyxl`.
- If `pandas` or `openpyxl` is missing, report the missing package before plotting.
- If running under WSL/Linux, explain that WSL Python usually cannot directly call Windows COM / Origin Automation.
- If Origin is not installed or COM launch fails, report that Origin automation is unavailable and do not claim plot generation.
- If the data has fewer than two numeric columns, stop with a clear message.
- If expected output files are missing, list them and exit nonzero.

## Notes for Codex

- Read `references/originpro_usage_notes.md` when diagnosing failures or adapting the template to a new workflow.
- Start from `scripts/check_origin_env.py` before attempting plotting.
- Adapt `scripts/plot_origin_template.py` to the user's real input, labels, graph template, and export formats.
- Prefer deterministic file existence checks over visual inspection.
- Keep diagnostics read-only except for writing reports under `output/`.
