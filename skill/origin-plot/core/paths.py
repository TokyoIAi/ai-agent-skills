"""Project-relative path helpers shared by the v1.0 core layer."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def rel(path: Path) -> str:
    """Return ``path`` rendered relative to the project root when possible."""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def resolve_project_path(value: str) -> Path:
    """Resolve ``value`` against the project root unless it is already absolute."""
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def current_timestamp_utc() -> str:
    """Return an ISO-8601 UTC timestamp (``YYYY-MM-DDTHH:MM:SSZ``)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
