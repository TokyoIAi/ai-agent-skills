"""Forward to the legacy ``scripts/test_cli_retry_injection.py``.

This shim keeps the v0.8.7 CLI retry-injection diagnostic reachable through
the new ``ops/`` layout without duplicating the implementation.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _runner import run_legacy  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run_legacy("test_cli_retry_injection.py"))
