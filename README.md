# ai-agent-skills

A personal collection of reusable AI Agent Skills for Codex, Claude Code, and local automation workflows.

## Skills

| Skill | Path | Status | Purpose |
|---|---|---|---|
| origin-plot | skill/origin-plot | v0.1 PASS | Automate Origin / OriginPro plotting with Windows Python and originpro |

## Repository layout

- skill/origin-plot/
- skill/origin-plot/.agents/skills/origin-plot/
- skill/origin-plot/data/
- skill/origin-plot/originext_smoke_test.py
- skill/origin-plot/originpro_smoke_test.py

## Design rule

Each Skill is stored as an independent subproject under skill/<skill-name>/ .

Generated output files are ignored by Git and are not uploaded by default.

## Current validated Skill

### origin-plot

Status: v0.1 PASS

Validated locally:

- Windows Python can import originpro.
- OriginExt COM smoke test passed.
- originpro smoke test passed.
- Origin worksheet creation succeeded.
- Origin graph export succeeded.
- PNG/PDF/OPJU generation succeeded locally.

## Quick start for origin-plot

Run from the repository root:

cd skill\origin-plot

Then run:

py .agents\skills\origin-plot\scripts\check_origin_env.py
py .agents\skills\origin-plot\scripts\plot_origin_template.py
