# v0.8.7 full stack reference

This directory exists as a documentation anchor for the **v1.0 core
refactor**. It records exactly which v0.8.7 surface the new ``core/`` and
``workflows/`` layer wraps without modifying.

The actual v0.8.7 source code lives unchanged at:

- ``scripts/`` — verified Origin executor, validator, batch script, hygiene
  tools, smoke tests, session utilities.
- ``configs/fitting/`` — canonical fitting configs.
- ``configs/errorbar/`` — canonical errorbar configs.
- ``configs/styles/`` and ``configs/exports/`` — reusable profiles.
- ``configs/batch/`` — verified batch configs.

The git history preserves the exact tree at tag
``v0.8.7-origin-plot-release-hygiene``. Use that tag if you need to
reproduce the v0.8.7 acceptance environment verbatim.

## Why we did not move the legacy code

The v0.8.7 stability work (retry loop, session health, history retention,
report path scanner, smoke tests) is the most heavily exercised part of the
Skill. Moving those files risks breaking the Origin control chain that the
README and CONTRIBUTING.md guarantee. Instead, ``core/`` and ``workflows/``
import or shell out to ``scripts/``, and ``ops/`` provides re-export shims
that point operators to the new layout while leaving the originals in place.

When the v1.0 layout has been live in production for at least one full
release cycle, the legacy ``scripts/`` may be moved into this archive and
replaced with proper modules under ``core/``.
