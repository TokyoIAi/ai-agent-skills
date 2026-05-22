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

py_cmd="python"
if command -v py >/dev/null 2>&1; then
    py_cmd="py"
fi

echo "Step 1/2: Running offline smoke tests (no Origin required)..."
"$py_cmd" scripts/run_smoke_tests.py --skip-origin
status=$?
if [ "$status" -ne 0 ]; then
    echo "FAIL: pre-commit smoke tests failed (exit $status)"
    exit 1
fi

echo ""
echo "Step 2/2: Scanning reports/ for absolute path leaks..."
"$py_cmd" scripts/check_committed_reports.py
status=$?
if [ "$status" -ne 0 ]; then
    echo "FAIL: pre-commit report path check failed (exit $status)"
    exit 1
fi

echo ""
echo "PASS: pre-commit smoke tests ok"
