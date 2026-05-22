"""Public origin-plot v1.0 workflow entry points.

Three small CLIs live here:

* ``run_plot.py`` - render a single plot from a config.
* ``run_batch.py`` - render multiple plots described by a batch YAML.
* ``accept_core.py`` - the minimal acceptance script for the core surface.

These workflows delegate to ``core/`` and the verified v0.8.7 ``scripts/``
implementation. Maintenance tooling lives under ``ops/``.
"""
