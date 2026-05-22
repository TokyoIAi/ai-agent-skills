# workflows/

The daily entry-point CLIs for `origin-plot`. **Start here.**

Every command below assumes you are at `skill/origin-plot/`.

| Script | Purpose |
|---|---|
| [`run_plot.py`](run_plot.py) | Render a single plot from a YAML config. |
| [`run_batch.py`](run_batch.py) | Render multiple plots from a batch YAML. |
| [`build_report_package.py`](build_report_package.py) | Rebuild `reports/report_package/` from an existing single-plot report. |
| [`accept_core.py`](accept_core.py) | Minimal acceptance suite (3 examples + path leak scan). |

## `run_plot.py` — single plot

```powershell
py workflows\run_plot.py --config configs\examples\line_plot.yaml
```

Pipeline:

1. Validate the YAML config against the v1.0 schema (delegates to
   `core/config_validator.py` which wraps the v0.8.7 validator).
2. Invoke the verified Origin executor
   (`scripts/origin_plot_from_config.py`).
3. Collect PNG / PDF / OPJU output paths from the legacy report.
4. Assemble `reports/report_package/` with figures, OPJU, configs, plus
   `figure_index.md` and `run_report.json`.

Exit status: 0 when the legacy executor reports `PASS`, `PASS with
warnings`, or `PASS with session_retry` **and** every requested output
exists on disk. Otherwise non-zero.

Useful flags:

- `--no-package` skips the report-package assembly. The single-plot
  report is still written to `reports/report_package/run_report.json`.

## `run_batch.py` — batch plotting

```powershell
py workflows\run_batch.py --batch-config configs\examples\batch.yaml
```

Reads a small batch YAML (`batch_name`, `continue_on_error`, `jobs[]`),
invokes `workflows/run_plot.py` per job, and writes
`reports/report_package/batch_report.json`. Failed jobs never prevent the
report from being written.

The verified v0.8.7 batch script (`scripts/origin_batch_plot.py`) remains
available for production batch runs that need `session_history_summary`,
`fit_artifact_summary`, and the other v0.8.x rollups. `workflows/run_batch.py`
is the v1.0 thin surface; pick the v0.8.x one when you need its richer
report.

## `accept_core.py` — minimal acceptance

```powershell
py workflows\accept_core.py
```

Runs `run_plot.py` against the three example configs
(`configs/examples/line_plot.yaml`, `errorbar_plot.yaml`,
`fitting_plot.yaml`), then runs the path leak scanner
(`ops/hygiene/check_committed_reports.py`).

Success line: `PASS: origin-plot core acceptance ok`.

Use this before tagging a v1.x patch or after any change that could
affect the public surface.

## `build_report_package.py` — rebuild a package

```powershell
py workflows\build_report_package.py
py workflows\build_report_package.py --report reports\origin_plot_v0_2_report.json
py workflows\build_report_package.py --report reports\origin_plot_v0_2_report.json --config configs\examples\line_plot.yaml
```

Reads a legacy single-plot report and copies the recorded outputs plus
the originating plot config into `reports/report_package/`. Useful when
the package was deleted or when you need to re-bundle outputs from a
previous run.

## What workflows do NOT do

- They do not parse Markdown, images, or unstructured input. The plot
  config must point at canonical CSV / XLSX / TSV / TXT data, and every
  required field must be set explicitly.
- They do not infer column roles or graph type. Both must be set in the
  YAML config.
- They do not retry on validation errors. If the data violates the
  canonical contract, the workflow exits non-zero with a clear message.

For the upstream side of this boundary, see
[`../contracts/codex_data_wrangler_contract.md`](../contracts/codex_data_wrangler_contract.md).

## Cross-links

- Codex contract: [`../contracts/README.md`](../contracts/README.md)
- Worked examples: [`../configs/examples/`](../configs/examples/)
- Maintenance tooling: [`../ops/README.md`](../ops/README.md)
- Verified backend: [`../scripts/`](../scripts/)
