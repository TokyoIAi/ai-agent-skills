# ai-agent-skills

A personal collection of reusable AI Agent Skills for Codex, Claude Code, and local automation workflows.

## Skills

| Skill | Path | Status | Purpose |
|---|---|---|---|
| origin-plot | skill/origin-plot | v0.9 Smart Data Understanding + Auto Plot | Smart input analysis (CSV/XLSX/TSV/TXT/Markdown) with automatic column-role inference, recommended graph type, generated plot config, and the existing config-based, batch, directory-scan, style-profiled, error-bar-capable, fitting-capable, fit-artifact-aware, Origin-session-resilient, retry-test-verified, session-health-monitored, timestamp-tracked, operator-tunable, and pre-commit-guarded OriginPro plotting pipeline. |

## Repository layout

- `skill/origin-plot/`
- `skill/origin-plot/.agents/skills/origin-plot/`
- `skill/origin-plot/configs/`
- `skill/origin-plot/scripts/`
- `skill/origin-plot/data/`

## Design rule

Each Skill is stored as an independent subproject under `skill/<skill-name>/`.

Generated output files are ignored by Git and are not uploaded by default.
