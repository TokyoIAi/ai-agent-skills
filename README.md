# ai-agent-skills

A personal collection of reusable AI Agent Skills for Codex, Claude Code, and local automation workflows.

## Skills

| Skill | Path | Status | Purpose |
|---|---|---|---|
| origin-plot | skill/origin-plot | v1.0-core-refactor | Stable Origin / OriginPro plot execution backend for canonical data and YAML configs, designed to be driven by Codex data-wrangling workflows. |

## Repository layout

- `skill/origin-plot/`
- `skill/origin-plot/core/`
- `skill/origin-plot/workflows/`
- `skill/origin-plot/contracts/`
- `skill/origin-plot/configs/`
- `skill/origin-plot/data/`
- `skill/origin-plot/scripts/`
- `skill/origin-plot/ops/`
- `skill/origin-plot/archive/`
- `skill/origin-plot/.agents/skills/origin-plot/`

## Design rule

Each Skill is stored as an independent subproject under `skill/<skill-name>/`.

Generated output files are ignored by Git and are not uploaded by default.

`origin-plot` v1.0 follows a strict separation of concerns:

- **Codex** is responsible for understanding messy inputs (complex Excel,
  Markdown, screenshots, lab-notebook photos), cleaning the data, and
  writing canonical CSV / YAML files.
- **origin-plot** receives canonical data + YAML and reliably renders PNG /
  PDF / OPJU through Origin / OriginPro.

See `skill/origin-plot/contracts/` for the formal contracts.
