# ops/

Advanced maintenance tooling that ships with origin-plot but is **not** part
of the daily core workflow. The day-to-day surface lives in `workflows/`.

| Subdirectory | Purpose |
|---|---|
| `ops/diagnostics/` | Test injection / retry path diagnostics. |
| `ops/health/` | Session history, health rollup, history reset. |
| `ops/smoke/` | Smoke test scripts and the aggregate runner. |
| `ops/hygiene/` | Pre-commit / report path leak guards. |
| `ops/release/` | Pre-commit shells used as release-time checks. |
| `ops/reports/` | Cross-report fit-artifact summaries. |

Each script under `ops/` is a thin re-export of the verified v0.8.7
implementation in `scripts/`. The scripts in `scripts/` remain functional;
`ops/` just gives operators a stable layout while the legacy entry points
finish their deprecation window.

If you only need to render a figure, ignore `ops/` entirely:

```powershell
py workflows\run_plot.py --config configs\examples\line_plot.yaml
```
