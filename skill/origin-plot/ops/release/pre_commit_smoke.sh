#!/usr/bin/env bash
# origin-plot v1.0 ops re-export of the verified pre-commit smoke runner.
# Delegates to scripts/pre_commit_smoke.sh.
set -e
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(dirname "$(dirname "$script_dir")")"
legacy="$project_root/scripts/pre_commit_smoke.sh"
if [ ! -f "$legacy" ]; then
    echo "FAIL: legacy pre_commit_smoke.sh missing at $legacy"
    exit 1
fi
bash "$legacy" "$@"
