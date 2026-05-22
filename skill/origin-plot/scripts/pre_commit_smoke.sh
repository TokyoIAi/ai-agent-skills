#!/usr/bin/env bash
# Pre-commit smoke runner for origin-plot.
# Manual invocation only; this script does not install Git hooks.
#
# Usage (from skill/origin-plot/):
#   bash scripts/pre_commit_smoke.sh

set -e

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(dirname "$script_dir")"

cd "$project_root"

echo "Running offline smoke tests (no Origin required)..."
if command -v py >/dev/null 2>&1; then
    py scripts/run_smoke_tests.py --skip-origin
else
    python scripts/run_smoke_tests.py --skip-origin
fi
status=$?
if [ "$status" -ne 0 ]; then
    echo "FAIL: pre-commit smoke tests failed (exit $status)"
    exit 1
fi
echo "PASS: pre-commit smoke tests ok"
