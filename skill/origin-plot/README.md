# origin-plot

`origin-plot` is a Codex Agent Skill for reproducible scientific plotting with Windows Python, `originpro`, and local Origin / OriginPro. It uses API automation, not GUI clicking, screenshot recognition, or mouse-coordinate automation.

Current version: v0.2.1.

## Supported formats

- CSV
- XLSX
- TSV
- TXT delimited text

Not formally supported in v0.2: old XLS unless `xlrd` is installed, OPJU as input, image data, and complex multi-layer Origin templates.

## Dependencies

Install into the Windows Python environment used by Codex:

```powershell
py -m pip install -r requirements.txt
```

## Environment detection

Run from `skill/origin-plot/`:

```powershell
py .agents\skills\origin-plot\scripts\check_origin_env.py
```

The report is written to `output/origin_env_report.json`.

## v0.1 sample plotting

```powershell
py .agents\skills\origin-plot\scripts\plot_origin_template.py
```

This reads `data/sample.csv` and writes sample PNG/PDF/OPJU files under `output/origin_plot/`.

## v0.2 config-based plotting

Validate the YAML first:

```powershell
py scripts\validate_origin_plot_config.py --config configs\origin_plot_config.yaml
```

Generate the plot:

```powershell
py scripts\origin_plot_from_config.py --config configs\origin_plot_config.yaml
```

## YAML fields

- `input_file`: input data path, usually relative to this subproject.
- `input_format`: `auto`, `csv`, `xlsx`, `tsv`, `txt`, or `xls`.
- `sheet_name`: Excel sheet name or null.
- `x_column`: column to use as X.
- `y_columns`: one or more Y columns.
- `graph_type`: `line`, `scatter`, or `line_symbol`.
- `graph_title`, `x_title`, `y_title`: Origin graph and axis titles.
- `output_dir`: output directory.
- `output_basename`: base filename for requested exports.
- `show_origin`: show or hide Origin while automating.
- `save_opju`, `export_png`, `export_pdf`: requested output switches.
- `png_width`: PNG export width in pixels.

## Outputs

The v0.2 script writes requested outputs such as:

- `output/origin_plot_config/sample_origin_plot.png`
- `output/origin_plot_config/sample_origin_plot.pdf`
- `output/origin_plot_config/sample_origin_plot.opju`
- `reports/origin_plot_v0_2_report.json`

`output/` is generated and ignored by Git. The report uses relative paths so it can be committed when useful.

## Manual Gate / First-run Origin Dialog

This skill does not automate GUI clicking.

Origin may show first-run, license, update, or initialization dialogs. The user may need to manually confirm such dialogs once before automation can proceed normally.

In the current v0.2.1 validation, the user reported one initial OK dialog, but a later PowerShell rerun completed without a popup. Therefore this is documented as first-run manual initialization, not a recurring automation blocker.

If a dialog appears on every run, treat the result as PARTIAL PASS until Origin configuration is fixed.

## Common errors

- `ModuleNotFoundError: originpro`: install dependencies into Windows Python.
- `Please install PyYAML`: run `py -m pip install pyyaml`.
- `Origin Automation / COM smoke test failed`: start Origin once as the same user, repair Origin if needed, then rerun environment detection.
- `Missing column(s)`: update the YAML to match the data headers.
- `at least 2 valid numeric rows`: clean the selected X/Y columns or choose numeric columns.

## Roadmap

- More graph templates and style presets.
- Multi-layer and multi-panel Origin output.
- Batch plotting from a directory of configs.
- Optional style reference files for journal-specific figures.
