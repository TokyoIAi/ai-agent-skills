# Canonical data contract

`origin-plot` v1.0 expects every input file to be a clean, table-shaped
dataset that can be loaded directly with `pandas.read_csv` /
`pandas.read_excel`. Codex (or any equivalent caller) is responsible for
producing that canonical form before invoking the workflows under
`workflows/`.

## Supported file formats

| Format | Suffix | Reader |
|---|---|---|
| CSV | `.csv` | `pandas.read_csv` |
| TSV | `.tsv` | `pandas.read_csv(sep="\t")` |
| TXT | `.txt` | `pandas.read_csv(sep=None, engine="python")` |
| Excel | `.xlsx` | `pandas.read_excel(engine="openpyxl")` |

`xls`, Markdown tables, OPJU input, and image OCR are explicitly **out of
scope** for the v1.0 core. If you need any of those, hand the data to Codex
first and let it produce a clean CSV / XLSX in `data/cleaned/`.

## File location

- Raw or upstream files live under `data/raw/` (git-ignored when bulky).
- Codex writes the canonical, plot-ready file under `data/cleaned/`.
- Worked examples that ship with the Skill live under `data/examples/`.

`origin-plot` only reads what `input_file` in the plot config points to.
Always use a project-relative path.

## Header row

- The first non-empty row is the header.
- Header cells must be unique strings.
- Avoid spaces and special characters that complicate downstream lookups,
  but Unicode is fine (`时间`, `电压`, etc. all work).

## Column conventions

- Numeric columns must contain only values that `pandas.to_numeric` can
  coerce. Empty cells are tolerated; the executor drops rows that become
  fully `NaN`.
- Units, when present, belong inside parentheses or square brackets at the
  end of the header (e.g. `电压(V)`, `intensity [a.u.]`). The validator
  reads the body of the column for plotting, so units do not have to be
  stripped from the header.
- Negative values are valid for plot data. **Error columns must be
  non-negative.**

## Error column convention

- For each Y series with uncertainty, add a sibling column with one of the
  documented error suffixes (`_err`, `_error`, `_uncertainty`, `误差`, or
  `标准差`). The executor treats `<y>_err` as the uncertainty for `<y>`.
- Map them in YAML via `y_error_columns`, e.g.

  ```yaml
  y_columns:
    - y
  y_error_columns:
    y: y_err
  ```

- An optional `x_error_column` is supported. Mark its column non-negative
  too.

## Group column convention

The v1.0 core ships line / scatter / line_symbol / errorbar plot types.
"Grouped" plots are out of scope for v1.0; if you need a group column,
**Codex pivots the data** into a wide CSV (one column per group level) before
handing it to the workflow.

## Sorting and ordering

- The executor does not sort rows. Codex must order the data by the X
  column before saving when monotonicity matters (e.g. line plots).
- Duplicate X values are kept as-is. If you need them merged, handle that
  upstream.

## Encoding

UTF-8 with no BOM is the safe default. PowerShell consoles may render
Chinese headers as garbled bytes when echoing files; the JSON / OPJU output
remains correctly encoded.

## Concrete examples

`data/examples/line_sample.csv` — minimal line plot data.
`data/examples/errorbar_sample.csv` — line + error column.
`data/examples/fitting_sample.csv` — line plot with a polynomial fit.

These are the smallest legal canonical inputs; treat them as the reference
shape when Codex generates new data.
