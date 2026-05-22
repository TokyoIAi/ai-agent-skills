# origin-plot

`origin-plot` is a Codex Agent Skill for reproducible scientific plotting with Windows Python, `originpro`, and local Origin / OriginPro. It uses API automation, not GUI clicking, screenshot recognition, or mouse-coordinate automation.

Current version: v0.4.

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

## v0.3 Batch Plotting

Batch plotting reads a batch YAML file that lists multiple single-plot YAML configs.

Default batch config:

```text
configs/batch/batch_plot_config.yaml
```

Run from `skill/origin-plot/`:

```powershell
py scripts\origin_batch_plot.py --batch-config configs\batch\batch_plot_config.yaml
```

Batch YAML fields:

- `batch_name`: name written to the batch report.
- `continue_on_error`: when true, a failed job is recorded and later jobs still run.
- `jobs`: non-empty list of jobs.
- `jobs[].name`: job name in the report.
- `jobs[].config`: path to a single-plot config YAML.

The batch report is written to:

```text
reports/origin_plot_v0_3_batch_report.json
```

Single job failures do not cause the batch script to exit without a report. The batch status is `PASS` when all jobs pass, `PARTIAL PASS` when some pass and some fail, and `FAIL` when all jobs fail.

## v0.4 Directory Scan and Auto Batch Config

Place multiple CSV/XLSX/TSV/TXT files under:

```text
data/batch_inputs/
```

Generate single-plot configs and a batch config:

```powershell
py scripts\generate_batch_configs_from_dir.py --scan-config configs\scan\scan_config.yaml
```

The scan step does not call Origin. It only reads data files, infers numeric X/Y columns, writes generated YAML configs, and writes `reports/origin_plot_v0_4_scan_report.json`.

Scan YAML fields:

- `scan_name`: name for generated batch and report.
- `input_dir`: directory to scan.
- `recursive`: scan nested directories when true.
- `input_formats`: allowed formats: `csv`, `xlsx`, `tsv`, `txt`.
- `x_column_strategy`: v0.4 supports `first_numeric`.
- `y_column_strategy`: v0.4 supports `remaining_numeric`.
- `graph_type`: default graph type for generated configs.
- `output_root`: output root used by generated plot configs.
- `generated_config_dir`: destination for generated single-plot YAML files.
- `generated_batch_config`: generated batch YAML path.
- `continue_on_error`: copied to the generated batch config.

Run the generated batch:

```powershell
py scripts\origin_batch_plot.py --batch-config configs\generated\generated_batch_config.yaml
```

The batch script performs the real Origin plotting. If any job fails, it writes `configs/generated/retry_failed_jobs.yaml` containing only failed jobs and records `retry_config` in `reports/origin_plot_v0_3_batch_report.json`.

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
- `reports/origin_plot_v0_3_batch_report.json`
- `reports/origin_plot_v0_4_scan_report.json`

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
