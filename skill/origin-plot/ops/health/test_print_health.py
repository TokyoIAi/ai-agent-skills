"""Forward to the legacy ``scripts/test_print_health.py``."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _runner import run_legacy  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run_legacy("test_print_health.py"))
