"""Pure-Python helpers for Origin session config, classification, and merging.

These utilities are extracted so they can be tested without calling Origin or
COM. They are imported by ``origin_plot_from_config.py`` and the v0.8.2 smoke
test ``test_session_retry_logic.py``.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


SESSION_ERROR_INDICATORS = (
    "\u65e0\u6548\u6307\u9488",  # 无效指针
    "ApplicationBase_LT_execute",
    "OriginExt",
    "originpro",
    "COMError",
    "com_error",
    "set_show",
    "_OriginExt",
    "Injected test OriginExt",
)
ORIGIN_PROCESS_NAMES = ("Origin64.exe", "Origin.exe", "OriginPro.exe")


SESSION_FIELDS = (
    "retry_on_com_error",
    "max_retries",
    "kill_stale_origin_before_retry",
    "retry_delay_seconds",
    "inject_session_error_once",
    "history_max_entries",
    "health",
)


def health_defaults() -> dict[str, Any]:
    return {
        "recent_window": 20,
        "degraded_ok_after_retry_threshold": 3,
        "degraded_failed_threshold": 1,
    }


def session_defaults() -> dict[str, Any]:
    return {
        "retry_on_com_error": True,
        "max_retries": 1,
        "kill_stale_origin_before_retry": True,
        "retry_delay_seconds": 2.0,
        "inject_session_error_once": False,
        "history_max_entries": 100,
        "health": health_defaults(),
    }


def coerce_health_policy(source: Any, context: str) -> dict[str, Any]:
    if source is None:
        return {}
    if not isinstance(source, dict):
        raise ValueError(f"{context}.health must be a mapping.")
    coerced: dict[str, Any] = {}
    if "recent_window" in source:
        try:
            value = int(source["recent_window"])
        except (TypeError, ValueError):
            raise ValueError(f"{context}.health.recent_window must be an integer.") from None
        if value < 1 or value > 10000:
            raise ValueError(f"{context}.health.recent_window must be between 1 and 10000.")
        coerced["recent_window"] = int(value)
    if "degraded_ok_after_retry_threshold" in source:
        try:
            value = int(source["degraded_ok_after_retry_threshold"])
        except (TypeError, ValueError):
            raise ValueError(
                f"{context}.health.degraded_ok_after_retry_threshold must be an integer."
            ) from None
        if value < 0 or value > 10000:
            raise ValueError(
                f"{context}.health.degraded_ok_after_retry_threshold must be between 0 and 10000."
            )
        coerced["degraded_ok_after_retry_threshold"] = int(value)
    if "degraded_failed_threshold" in source:
        try:
            value = int(source["degraded_failed_threshold"])
        except (TypeError, ValueError):
            raise ValueError(
                f"{context}.health.degraded_failed_threshold must be an integer."
            ) from None
        if value < 0 or value > 10000:
            raise ValueError(
                f"{context}.health.degraded_failed_threshold must be between 0 and 10000."
            )
        coerced["degraded_failed_threshold"] = int(value)
    return coerced


def cli_health_overrides(
    recent_window: Any | None = None,
    degraded_ok_after_retry_threshold: Any | None = None,
    degraded_failed_threshold: Any | None = None,
) -> dict[str, int]:
    """Build a validated CLI health override dict (only set fields included)."""
    payload: dict[str, Any] = {}
    if recent_window is not None:
        payload["recent_window"] = recent_window
    if degraded_ok_after_retry_threshold is not None:
        payload["degraded_ok_after_retry_threshold"] = degraded_ok_after_retry_threshold
    if degraded_failed_threshold is not None:
        payload["degraded_failed_threshold"] = degraded_failed_threshold
    return coerce_health_policy(payload, "cli.health") if payload else {}


def compute_health_snapshot(
    history_path: Path,
    rel_history_path: str,
    policy: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Read session_history.json (if present) and compute a health snapshot.

    ``rel_history_path`` is the project-relative path string emitted in the
    snapshot (callers compute it via their own ``rel`` helper).
    """
    import json as _json

    effective_policy: dict[str, int] = dict(health_defaults())
    if policy:
        for key in effective_policy:
            if key in policy:
                try:
                    effective_policy[key] = int(policy[key])
                except (TypeError, ValueError):
                    pass

    snapshot: dict[str, Any] = {
        "history_path": rel_history_path,
        "entries_seen": 0,
        "recent_window": effective_policy["recent_window"],
        "degraded_ok_after_retry_threshold": effective_policy[
            "degraded_ok_after_retry_threshold"
        ],
        "degraded_failed_threshold": effective_policy["degraded_failed_threshold"],
        "recent_ok": 0,
        "recent_ok_after_retry": 0,
        "recent_failed": 0,
        "recent_injection_triggered": 0,
        "health_status": "unknown",
    }

    if not history_path.exists():
        return snapshot
    try:
        raw = history_path.read_text(encoding="utf-8")
        entries = _json.loads(raw)
    except (OSError, _json.JSONDecodeError):
        return snapshot
    if not isinstance(entries, list):
        return snapshot

    snapshot["entries_seen"] = len(entries)
    window = effective_policy["recent_window"]
    recent = entries[-int(window):] if window > 0 else []
    for entry in recent:
        if not isinstance(entry, dict):
            continue
        fss = str(entry.get("final_session_status") or "")
        if fss == "ok":
            snapshot["recent_ok"] += 1
        elif fss == "ok_after_retry":
            snapshot["recent_ok_after_retry"] += 1
        elif fss == "failed":
            snapshot["recent_failed"] += 1
        if entry.get("injection_triggered"):
            snapshot["recent_injection_triggered"] += 1

    if snapshot["recent_failed"] >= effective_policy["degraded_failed_threshold"]:
        snapshot["health_status"] = "degraded"
    elif (
        snapshot["recent_ok_after_retry"]
        >= effective_policy["degraded_ok_after_retry_threshold"]
    ):
        snapshot["health_status"] = "degraded"
    else:
        snapshot["health_status"] = "ok"
    return snapshot


def _coerce_session_dict(source: dict[str, Any], context: str) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise ValueError(f"{context} must be a mapping.")
    coerced: dict[str, Any] = {}
    if "retry_on_com_error" in source:
        value = source["retry_on_com_error"]
        if not isinstance(value, bool):
            raise ValueError(f"{context}.retry_on_com_error must be a boolean.")
        coerced["retry_on_com_error"] = bool(value)
    if "max_retries" in source:
        try:
            value = int(source["max_retries"])
        except (TypeError, ValueError):
            raise ValueError(f"{context}.max_retries must be an integer.") from None
        if value < 0 or value > 5:
            raise ValueError(f"{context}.max_retries must be between 0 and 5.")
        coerced["max_retries"] = int(value)
    if "kill_stale_origin_before_retry" in source:
        value = source["kill_stale_origin_before_retry"]
        if not isinstance(value, bool):
            raise ValueError(f"{context}.kill_stale_origin_before_retry must be a boolean.")
        coerced["kill_stale_origin_before_retry"] = bool(value)
    if "retry_delay_seconds" in source:
        try:
            value = float(source["retry_delay_seconds"])
        except (TypeError, ValueError):
            raise ValueError(f"{context}.retry_delay_seconds must be a number.") from None
        if value < 0 or value > 60:
            raise ValueError(f"{context}.retry_delay_seconds must be between 0 and 60.")
        coerced["retry_delay_seconds"] = float(value)
    if "inject_session_error_once" in source:
        value = source["inject_session_error_once"]
        if not isinstance(value, bool):
            raise ValueError(f"{context}.inject_session_error_once must be a boolean.")
        coerced["inject_session_error_once"] = bool(value)
    if "history_max_entries" in source:
        raw_value = source["history_max_entries"]
        # Accept None / 0 with a fallback to default to avoid unbounded growth.
        if raw_value is None or raw_value == 0:
            coerced["history_max_entries"] = 100
        else:
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                raise ValueError(f"{context}.history_max_entries must be an integer.") from None
            if value < 1 or value > 10000:
                raise ValueError(f"{context}.history_max_entries must be between 1 and 10000.")
            coerced["history_max_entries"] = int(value)
    if "health" in source:
        coerced["health"] = coerce_health_policy(source["health"], context)
    return coerced


def merge_session_settings(
    profile: dict[str, Any] | None,
    explicit: dict[str, Any] | None,
    cli_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Combine session settings with priority: defaults < profile < explicit < CLI."""
    merged = session_defaults()
    health = dict(merged.get("health") or health_defaults())
    for source, context in (
        (profile, "session_profile"),
        (explicit, "origin_session"),
        (cli_overrides, "cli"),
    ):
        if not source:
            continue
        coerced = _coerce_session_dict(source, context)
        if "health" in coerced:
            health.update(coerced.pop("health"))
        merged.update(coerced)
    merged["health"] = health
    return merged


def normalize_session_config(config: dict[str, Any]) -> dict[str, Any]:
    """Backward-compatible entry point for plot configs lacking session_profile."""
    explicit = config.get("origin_session") or {}
    return merge_session_settings(None, explicit)


def is_session_error(exc: BaseException) -> bool:
    text = f"{type(exc).__module__}.{type(exc).__name__}: {exc}"
    return any(indicator.lower() in text.lower() for indicator in SESSION_ERROR_INDICATORS)


def kill_stale_origin_processes() -> tuple[bool, list[str]]:
    notes: list[str] = []
    killed_any = False
    for proc_name in ORIGIN_PROCESS_NAMES:
        try:
            completed = subprocess.run(
                ["taskkill", "/F", "/IM", proc_name],
                capture_output=True,
                text=True,
                check=False,
            )
            stdout = (completed.stdout or "").strip()
            stderr = (completed.stderr or "").strip()
            if completed.returncode == 0:
                killed_any = True
                if stdout:
                    notes.append(f"taskkill {proc_name}: {stdout}")
            elif stdout or stderr:
                lower_combo = (stdout + " " + stderr).lower()
                if "not found" not in lower_combo and "\u672a\u627e\u5230" not in (stdout + stderr):
                    notes.append(f"taskkill {proc_name} rc={completed.returncode}: {stdout or stderr}")
        except FileNotFoundError:
            notes.append("taskkill.exe is not available; skipped Origin process kill")
            break
        except Exception as exc:  # noqa: BLE001 - never raise from cleanup
            notes.append(f"taskkill {proc_name} failed: {type(exc).__name__}: {exc}")
    return killed_any, notes


class InjectedSessionError(RuntimeError):
    """Marker error for the test-only session error injection path."""


def make_injected_session_error() -> InjectedSessionError:
    return InjectedSessionError(
        "Injected test OriginExt ApplicationBase_LT_execute \u65e0\u6548\u6307\u9488"
    )


def load_session_profile(path_value: str, project_root: Path) -> tuple[str, dict[str, Any]]:
    candidate = Path(path_value)
    if candidate.is_absolute():
        raise ValueError(f"session_profile must be relative: {path_value}")
    resolved = (project_root / candidate).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"session_profile does not exist: {path_value}")
    try:
        import yaml
    except ModuleNotFoundError:  # pragma: no cover - PyYAML is a hard dep elsewhere
        raise RuntimeError("Please install PyYAML: py -m pip install pyyaml") from None
    with resolved.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"session_profile must be a YAML mapping: {path_value}")
    # Strip presentational keys before merging.
    cleaned = {key: value for key, value in data.items() if key in SESSION_FIELDS}
    try:
        rel_path = str(resolved.relative_to(project_root))
    except ValueError:
        rel_path = str(resolved)
    return rel_path, cleaned
