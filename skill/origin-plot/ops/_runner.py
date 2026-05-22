"""Helper used by ops/* shims to invoke a legacy script with current argv."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGACY_SCRIPTS = PROJECT_ROOT / "scripts"


def run_legacy(name: str) -> int:
    target = LEGACY_SCRIPTS / name
    if not target.exists():
        print(f"FAIL: legacy script missing: {target.relative_to(PROJECT_ROOT)}")
        return 1
    # Preserve argv: legacy scripts use ``argparse`` so we forward as-is.
    sys.argv[0] = str(target)
    if str(LEGACY_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(LEGACY_SCRIPTS))
    try:
        runpy.run_path(str(target), run_name="__main__")
    except SystemExit as exc:
        code = exc.code
        if isinstance(code, int):
            return code
        if code is None:
            return 0
        return 1
    return 0
