# Codex data-wrangler contract

`origin-plot` v1.0 receives canonical data and a YAML config. It does **not**
attempt to understand messy spreadsheets, Markdown tables, photographs of
notebooks, or auto-infer column roles. Those responsibilities sit upstream
with Codex (or any equivalent caller).

> origin-plot receives canonical data and config. Codex handles
> messy/raw data understanding before invoking origin-plot.

## Codex responsibilities

When the user hands the system a non-canonical artifact, Codex must:

1. **Read** the upstream artifact, regardless of format
   (Excel with multiple sheets, Markdown tables, screenshots, raw lab
   notebooks, etc.).
2. **Clean** the data: align units, normalise column names, drop empty
   rows, fix obvious typos.
3. **Standardise** to the canonical shape described in
   `canonical_data_contract.md`.
4. **Persist** the cleaned dataset as `data/cleaned/<dataset>.csv` (or
   `.xlsx` if multi-sheet output is required).
5. **Generate** a plot config under `configs/generated/<dataset>.yaml`
   conforming to `plot_config_schema.md`.
6. **Decide** the figure intent: which X / Y / error columns to use, what
   graph type, what titles, which style and export profiles.
7. **Invoke** the workflow:

   ```powershell
   py workflows\run_plot.py --config configs\generated\<dataset>.yaml
   ```

8. **Inspect** the run report at `reports/report_package/run_report.json`
   and surface PASS / FAIL plus the figure paths back to the user.

## origin-plot responsibilities

`origin-plot` v1.0 commits to:

- Validating `plot_config.yaml` against the schema in
  `plot_config_schema.md`.
- Loading canonical data (CSV / XLSX / TSV / TXT) via `core/data_loader.py`.
- Driving Origin / OriginPro through the verified executor in
  `scripts/origin_plot_from_config.py`.
- Exporting PNG / PDF / OPJU and assembling the report package.
- Writing minimal, reproducible run reports.

That is the entire scope. If a user asks for image OCR, ML-based
intent inference, multi-panel figures, or grouped pivots, Codex must do the
work and feed `origin-plot` a canonical CSV plus an explicit config.

## Out of scope for origin-plot v1.0

- OCR or handwriting recognition.
- Photo-of-table parsing.
- Generic "guess the user's intent" inference.
- Markdown / OPJU / image input formats (Codex must convert beforehand).
- Grouped / faceted / multi-panel plotting (Codex pivots into wide form
  beforehand if needed).
- Long-term health monitoring (still available but moved under
  `ops/health/`).

## Interaction sketch

```
user --> Codex: "Plot this Excel sheet as voltage vs current"
Codex --> data/cleaned/voltage_current.csv
Codex --> configs/generated/voltage_current.yaml
Codex --> py workflows\run_plot.py --config configs\generated\voltage_current.yaml
workflows --> Origin (via scripts/origin_plot_from_config.py)
workflows --> reports/report_package/{figures,origin_projects,configs,figure_index.md,run_report.json}
Codex --> user: "Done. PNG at reports/report_package/figures/voltage_current.png"
```

Anything that violates this contract should be caught early, either in
Codex's planning step or in the validator (which fails fast on missing
columns, non-numeric data, or unsupported graph types).
