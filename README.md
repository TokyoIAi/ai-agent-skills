# ai-agent-skills

A personal collection of reusable AI Agent Skills for Codex, Claude Code, and local automation workflows.

## Skills

| Skill | Path | Status | Purpose |
|---|---|---|---|
| origin-plot | skill/origin-plot | v0.6 Error Bar MVP | Config-based, batch, directory-scan, style-profiled, and error-bar-capable Origin / OriginPro plotting with CSV/XLSX/TSV/TXT input. |

## Repository layout

- `skill/origin-plot/`
- `skill/origin-plot/.agents/skills/origin-plot/`
- `skill/origin-plot/configs/`
- `skill/origin-plot/scripts/`
- `skill/origin-plot/data/`

## Design rule

Each Skill is stored as an independent subproject under `skill/<skill-name>/`.

Generated output files are ignored by Git and are not uploaded by default.
