"""Scan ``reports/`` for absolute path leaks before commit.

Run from ``skill/origin-plot/``:

    py scripts\\check_committed_reports.py

Exit codes:
    0 - no absolute paths detected (PASS)
    1 - leaks detected or scan error (FAIL)

Scans text-like files under ``reports/`` for Windows-style and POSIX-style
absolute paths that often indicate machine-local state was accidentally
committed. The script never edits any file. ``output/`` is intentionally not
scanned because it is git-ignored.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORTS_DIR = PROJECT_ROOT / "reports"
SUPPORTED_SUFFIXES = {".json", ".csv", ".md", ".txt"}
DEFAULT_SKIP_NAMES = {"session_history.bak.json"}

# Patterns that flag absolute or machine-local paths leaking into reports.
# Drive-letter forms like ``H:\``, ``C:/``, plus POSIX mounts like ``/mnt/``.
LEAK_PATTERNS = (
    re.compile(r"[A-Za-z]:\\\\"),   # JSON-escaped Windows drive backslash, e.g. "H:\\"
    re.compile(r"[A-Za-z]:\\"),     # raw Windows drive backslash in CSV/Markdown
    re.compile(r"[A-Za-z]:/"),      # forward-slash form, e.g. ``H:/``
    re.compile(r"/mnt/"),           # WSL-style mount path
)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def discover_files(reports_dir: Path, skip_bak: bool) -> list[Path]:
    if not reports_dir.exists():
        return []
    files: list[Path] = []
    for path in sorted(reports_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if path.name in DEFAULT_SKIP_NAMES:
            continue
        if skip_bak and path.suffix.lower() == ".bak":
            continue
        if skip_bak and path.name.endswith(".bak.json"):
            continue
        files.append(path)
    return files


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    findings: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        findings.append((0, "READ_ERROR", f"{type(exc).__name__}: {exc}"))
        return findings
    for line_no, line in enumerate(text.splitlines(), start=1):
        for pattern in LEAK_PATTERNS:
            match = pattern.search(line)
            if match:
                snippet = line.strip()
                if len(snippet) > 200:
                    snippet = snippet[:200] + "..."
                findings.append((line_no, match.group(0), snippet))
                break
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan reports/ for absolute path leaks before commit."
    )
    parser.add_argument(
        "--reports-dir",
        default="reports",
        help="Reports directory to scan (relative to project root).",
    )
    parser.add_argument(
        "--include-bak",
        action="store_true",
        help="Also scan .bak / .bak.json siblings (skipped by default).",
    )
    args = parser.parse_args()

    reports_dir = (PROJECT_ROOT / args.reports_dir).resolve() if not Path(args.reports_dir).is_absolute() else Path(args.reports_dir)
    skip_bak = not args.include_bak
    files = discover_files(reports_dir, skip_bak=skip_bak)

    if not files:
        print(f"PASS: no scannable files under {rel(reports_dir)}")
        return 0

    leaks: list[tuple[Path, list[tuple[int, str, str]]]] = []
    for path in files:
        findings = scan_file(path)
        if findings:
            leaks.append((path, findings))

    if leaks:
        print(f"FAIL: absolute path leaks detected in {len(leaks)} file(s)")
        for path, findings in leaks:
            for line_no, match, snippet in findings:
                print(f"- {rel(path)}:{line_no} match={match!r} snippet={snippet!r}")
        return 1

    print(f"scanned {len(files)} file(s) under {rel(reports_dir)}")
    print("PASS: committed report path check ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
