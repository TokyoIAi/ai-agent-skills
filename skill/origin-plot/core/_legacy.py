"""Internal helper that exposes the proven v0.8.7 ``scripts/`` modules to the
v1.0 ``core`` layer without duplicating logic.

The Skill's verified Origin control implementation lives under
``skill/origin-plot/scripts/``. The ``core`` layer wraps those modules so the
public ``workflows/`` entry points can stay thin, while the freezing-tested
behavior remains the single source of truth.
"""
from __future__ import annotations

import sys

from .paths import PROJECT_ROOT

# Add ``scripts/`` to ``sys.path`` exactly once. We do not move the legacy
# modules; we only borrow them.
_SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
