# Pre-commit smoke runner for origin-plot.
# Manual invocation only; this script does not install Git hooks.
#
# Usage (from skill/origin-plot/):
#   powershell -ExecutionPolicy Bypass -File scripts\pre_commit_smoke.ps1

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

Push-Location $projectRoot
try {
    Write-Host "Running offline smoke tests (no Origin required)..."
    py scripts\run_smoke_tests.py --skip-origin
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Host "FAIL: pre-commit smoke tests failed (exit $code)"
        exit 1
    }
    Write-Host "PASS: pre-commit smoke tests ok"
    exit 0
}
finally {
    Pop-Location
}
