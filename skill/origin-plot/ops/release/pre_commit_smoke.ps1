# origin-plot v1.0 ops re-export of the verified pre-commit smoke runner.
# Delegates to scripts/pre_commit_smoke.ps1 so the v0.8.7 implementation
# remains the source of truth.

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$legacy = Join-Path $projectRoot "scripts/pre_commit_smoke.ps1"

if (-not (Test-Path $legacy)) {
    Write-Host "FAIL: legacy pre_commit_smoke.ps1 missing at $legacy"
    exit 1
}

powershell -ExecutionPolicy Bypass -File $legacy @args
exit $LASTEXITCODE
