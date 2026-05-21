"""Diagnose whether Windows Python can automate Origin/OriginPro via originpro.

This script is intentionally read-only for system state. It only writes a JSON
report under output/origin_env_report.json.
"""

from __future__ import annotations

import importlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]
REPORT_PATH = PROJECT_ROOT / "output" / "origin_env_report.json"


def import_status(module_name: str) -> tuple[bool, str | None, str | None]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostics should preserve root cause
        return False, None, f"{type(exc).__name__}: {exc}"
    version = getattr(module, "__version__", None)
    return True, str(version) if version is not None else None, None


def existing_originlab_paths() -> list[str]:
    candidates = [
        Path(r"C:\Program Files\OriginLab"),
        Path(r"C:\Program Files (x86)\OriginLab"),
        Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
    ]

    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")

    found: list[str] = []
    for candidate in candidates:
        if not candidate.exists():
            continue
        if candidate.name == "Programs":
            try:
                matches = [
                    path
                    for path in candidate.rglob("*")
                    if "origin" in path.name.lower() or "originlab" in str(path).lower()
                ]
            except OSError:
                matches = []
            found.extend(str(path) for path in matches[:25])
        else:
            found.append(str(candidate))
            try:
                found.extend(str(path) for path in candidate.iterdir())
            except OSError:
                pass

    return sorted(dict.fromkeys(found))


def start_menu_origin_targets() -> list[str]:
    if platform.system().lower() != "windows":
        return []

    script = r"""
$shell = New-Object -ComObject WScript.Shell
$locations = @(
  "C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
  "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
)
foreach ($location in $locations) {
  Get-ChildItem $location -Filter *.lnk -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match "Origin|OriginLab" -or $_.Name -match "Origin|OriginLab" } |
    ForEach-Object {
      try {
        $shortcut = $shell.CreateShortcut($_.FullName)
        if ($shortcut.TargetPath) { $shortcut.TargetPath }
      } catch {}
    }
}
"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception:
        return []

    targets = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return sorted(dict.fromkeys(targets))


def run_python_smoke(code: str, timeout: int = 120) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [sys.executable, "-u", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": None,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "error": f"TimeoutExpired after {timeout} seconds",
        }
    except Exception as exc:  # noqa: BLE001 - diagnostics must keep exact failure
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def originext_smoke(originext_import_ok: bool, is_windows: bool) -> dict[str, Any]:
    if not is_windows:
        return {"ok": False, "error": "skipped: not Windows", "stdout": "", "stderr": ""}
    if not originext_import_ok:
        return {"ok": False, "error": "skipped: OriginExt import failed", "stdout": "", "stderr": ""}
    return run_python_smoke(
        r'''
import faulthandler
import traceback
faulthandler.enable()
faulthandler.dump_traceback_later(90, exit=True)
app = None
try:
    import OriginExt as O
    app = O.Application()
    app.Visible = 0
    app.LT_execute('type -b "OriginExt COM OK";')
    try:
        app.Exit()
    except Exception:
        pass
    print("PASS: OriginExt COM smoke ok")
except Exception:
    print("FAIL: OriginExt COM smoke failed")
    traceback.print_exc()
    raise
finally:
    try:
        if app is not None:
            app.Exit()
    except Exception:
        pass
''',
        timeout=120,
    )


def originpro_smoke(originpro_import_ok: bool, is_windows: bool) -> dict[str, Any]:
    if not is_windows:
        return {"ok": False, "error": "skipped: not Windows", "stdout": "", "stderr": ""}
    if not originpro_import_ok:
        return {"ok": False, "error": "skipped: originpro import failed", "stdout": "", "stderr": ""}
    return run_python_smoke(
        r'''
import faulthandler
import traceback
faulthandler.enable()
faulthandler.dump_traceback_later(90, exit=True)
op = None
try:
    import originpro as op
    op.set_show(False)
    wks = op.new_sheet()
    print(f"PASS: originpro smoke ok: {wks}")
except Exception:
    print("FAIL: originpro smoke failed")
    traceback.print_exc()
    raise
finally:
    try:
        if op is not None:
            op.exit()
    except Exception:
        pass
''',
        timeout=120,
    )


def main() -> int:
    is_windows = platform.system().lower() == "windows"
    python_bits = "64bit" if sys.maxsize > 2**32 else "32bit"
    originext_ok, originext_version, originext_error = import_status("OriginExt")
    originpro_ok, originpro_version, originpro_error = import_status("originpro")
    pandas_ok, pandas_version, pandas_error = import_status("pandas")
    openpyxl_ok, openpyxl_version, openpyxl_error = import_status("openpyxl")
    originlab_paths = existing_originlab_paths() if is_windows else []
    origin_shortcut_targets = start_menu_origin_targets() if is_windows else []
    origin_install_path_found = bool(originlab_paths or origin_shortcut_targets)
    originext_probe = originext_smoke(originext_ok, is_windows)
    originpro_probe = originpro_smoke(originpro_ok, is_windows)
    originext_com_smoke_ok = bool(originext_probe.get("ok"))
    originpro_smoke_ok = bool(originpro_probe.get("ok"))
    python_dependencies_ok = bool(pandas_ok and originpro_ok)
    ready_csv = bool(
        is_windows
        and pandas_ok
        and originpro_ok
        and origin_install_path_found
        and originpro_smoke_ok
    )
    ready_excel = bool(
        is_windows
        and pandas_ok
        and openpyxl_ok
        and originpro_ok
        and origin_install_path_found
        and originpro_smoke_ok
    )
    ready = bool(originpro_smoke_ok or originext_com_smoke_ok)

    missing_requirements: list[str] = []
    if not is_windows:
        missing_requirements.append("Windows Python is required for Origin COM automation.")
    if not originpro_ok:
        missing_requirements.append("Python package missing: originpro")
    if not pandas_ok:
        missing_requirements.append("Python package missing: pandas")
    if not openpyxl_ok:
        missing_requirements.append("Python package missing: openpyxl")
    if not origin_install_path_found:
        missing_requirements.append(
            "No common OriginLab install path found. This can be a possible false negative; "
            "confirm Origin/OriginPro is installed and registered for automation."
        )
    if not ready:
        missing_requirements.append(
            "Origin Automation / COM smoke test failed. Import success alone is not enough."
        )

    report: dict[str, Any] = {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "python_bits": python_bits,
        "platform": platform.platform(),
        "is_windows": is_windows,
        "is_wsl": "microsoft" in platform.release().lower()
        or "microsoft" in platform.version().lower(),
        "python_dependencies_ok": python_dependencies_ok,
        "origin_install_path_found": origin_install_path_found,
        "originext_import_ok": originext_ok,
        "originext_version": originext_version,
        "originext_error": originext_error,
        "originext_com_smoke_ok": originext_com_smoke_ok,
        "originext_com_smoke_stdout": originext_probe.get("stdout"),
        "originext_com_smoke_stderr": originext_probe.get("stderr"),
        "originext_com_smoke_error": originext_probe.get("error"),
        "originpro_import_ok": originpro_ok,
        "originpro_version": originpro_version,
        "originpro_error": originpro_error,
        "originpro_smoke_ok": originpro_smoke_ok,
        "originpro_smoke_stdout": originpro_probe.get("stdout"),
        "originpro_smoke_stderr": originpro_probe.get("stderr"),
        "originpro_smoke_error": originpro_probe.get("error"),
        "pandas_import_ok": pandas_ok,
        "pandas_version": pandas_version,
        "pandas_error": pandas_error,
        "openpyxl_import_ok": openpyxl_ok,
        "openpyxl_version": openpyxl_version,
        "openpyxl_error": openpyxl_error,
        "originlab_paths_found": originlab_paths,
        "origin_shortcut_targets_found": origin_shortcut_targets,
        "ready_for_csv_origin_plot": ready_csv,
        "ready_for_excel_origin_plot": ready_excel,
        "ready_for_origin_automation": ready,
        "missing_requirements": missing_requirements,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Environment report written to: {REPORT_PATH}")
    if not ready:
        print("Origin automation is not ready. Missing requirements:")
        for item in missing_requirements:
            print(f"- {item}")
        print("Suggested package install command: py -m pip install originpro pandas openpyxl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
