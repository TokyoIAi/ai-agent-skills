"""origin-plot core execution layer.

The ``core`` package collects the small handful of responsibilities that the
Skill keeps after the v1.0 refactor:

* config validation
* canonical data loading
* style / export profile lookups
* the Origin executor (delegates to the verified v0.8.7 implementation)
* report writers (single-plot, batch, report_package)

It deliberately stays a thin layer: the proven ``scripts/`` modules that ship
with v0.8.7 remain the source of truth for Origin control. ``core`` re-exports
those entry points so future cleanup can happen without breaking workflows.
"""
