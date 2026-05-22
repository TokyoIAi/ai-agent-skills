"""Reset reports/session_history.json before recording fresh health metrics.

Run from ``skill/origin-plot/``:

    py scripts\\reset_session_history.py

Behavior:
- Backs up the existing file to ``reports/session_history.bak.json`` (overwriting any
  prior backup) before truncating.
- Writes an empty JSON array ``[]`` to ``reports/session_history.json``.
- Prints ``PASS: session history reset`` on success.
- Does not touch any other report or output file.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HISTORY_PATH = PROJECT_ROOT / "reports" / "session_history.json"
BACKUP_PATH = PROJECT_ROOT / "reports" / "session_history.bak.json"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def reset() -> int:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if HISTORY_PATH.exists():
        try:
            shutil.copyfile(HISTORY_PATH, BACKUP_PATH)
            print(f"backup: {rel(BACKUP_PATH)}")
        except Exception as exc:  # noqa: BLE001 - report and continue with reset
            print(f"WARN: backup failed: {type(exc).__name__}: {exc}")
    try:
        HISTORY_PATH.write_text(json.dumps([], indent=2), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - reset must surface failure clearly
        print(f"FAIL: could not write {rel(HISTORY_PATH)}: {type(exc).__name__}: {exc}")
        return 1
    print(f"reset: {rel(HISTORY_PATH)}")
    print("PASS: session history reset")
    return 0


if __name__ == "__main__":
    raise SystemExit(reset())
