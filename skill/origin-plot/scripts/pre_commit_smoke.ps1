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
    Write-Host "Step 1/2: Running offline smoke tests (no Origin required)..."
    py scripts\run_smoke_tests.py --skip-origin
    $smokeCode = $LASTEXITCODE
    if ($smokeCode -ne 0) {
        Write-Host "FAIL: pre-commit smoke tests failed (exit $smokeCode)"
        exit 1
    }

    Write-Host ""
    Write-Host "Step 2/2: Scanning reports/ for absolute path leaks..."
    py scripts\check_committed_reports.py
    $checkCode = $LASTEXITCODE
    if ($checkCode -ne 0) {
        Write-Host "FAIL: pre-commit report path check failed (exit $checkCode)"
        exit 1
    }

    Write-Host ""
    Write-Host "PASS: pre-commit smoke tests ok"
    exit 0
}
finally {
    Pop-Location
}
