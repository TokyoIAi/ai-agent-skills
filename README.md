# ai-agent-skills

A personal collection of reusable AI Agent Skills for Codex, Claude Code, and local automation workflows.

## Skills

| Skill | Path | Status | Purpose |
|---|---|---|---|
| origin-plot | skill/origin-plot | v0.7 Curve Fitting MVP | Config-based, batch, directory-scan, style-profiled, error-bar-capable, and fitting-capable Origin / OriginPro plotting with CSV/XLSX/TSV/TXT input. |

## Repository layout

- `skill/origin-plot/`
- `skill/origin-plot/.agents/skills/origin-plot/`
- `skill/origin-plot/configs/`
- `skill/origin-plot/scripts/`
- `skill/origin-plot/data/`

## Design rule

Each Skill is stored as an independent subproject under `skill/<skill-name>/`.

Generated output files are ignored by Git and are not uploaded by default.
