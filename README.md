# ai-agent-skills

A personal collection of reusable AI Agent Skills for Codex, Claude Code,
and local automation workflows. Each Skill is an independent subproject
under `skill/<skill-name>/`. Generated outputs are git-ignored and never
uploaded by default.

## Skills

| Skill | Path | Status | Purpose |
|---|---|---|---|
| origin-plot | [`skill/origin-plot/`](skill/origin-plot/) | v1.0.1 Core Execution Backend | Stable Origin / OriginPro plot execution backend for canonical data + YAML configs. |

For setup, daily commands, the data-handling boundary with Codex, and the
directory map, read [`skill/origin-plot/README.md`](skill/origin-plot/README.md).

## Branch and tag conventions

- Active development happens on the `skill` branch.
- Feature releases tag as `vX.Y-<skill>-<short-name>` (e.g.
  `v1.0-origin-plot-core-refactor`); hardening or doc patches tag as
  `vX.Y.Z-...` (e.g. `v1.0.1-origin-plot-core-archive-notes`).
- Historical experiments (such as v0.9 smart-input) are preserved by
  immutable tags plus frozen archive branches; they are intentionally
  out of the v1.0+ mainline. See
  [`skill/origin-plot/archive/v0_9_smart_input_reference.md`](skill/origin-plot/archive/v0_9_smart_input_reference.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the smoke-test routine,
pre-commit hygiene, and the rule that `output/` must never be committed.
