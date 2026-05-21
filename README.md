# origin-plot-skill

A Codex Agent Skill for automating Origin / OriginPro plotting through Windows Python and the originpro package.

## Repository layout

- skill/origin-plot/.agents/skills/origin-plot/
- skill/origin-plot/data/
- skill/origin-plot/originext_smoke_test.py
- skill/origin-plot/originpro_smoke_test.py

## Quick start

Run from the repository root:

cd skill\origin-plot

Then run:

py .agents\skills\origin-plot\scripts\check_origin_env.py
py .agents\skills\origin-plot\scripts\plot_origin_template.py

## Status

v0.1 has been locally validated:

- Windows Python can import originpro.
- OriginExt COM smoke test passed.
- originpro smoke test passed.
- Origin worksheet, graph export, PNG/PDF/OPJU generation succeeded locally.

Generated output files are ignored by Git and are not uploaded by default.
