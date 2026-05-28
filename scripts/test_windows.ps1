param(
    [switch]$RequireApiKeys
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "未找到虚拟环境，请先运行 scripts\install_windows.ps1" -ForegroundColor Red
    exit 1
}

Set-Location $RepoRoot

$DoctorArgs = @("-m", "core.dependency_check", "--repo-root", $RepoRoot)
if ($RequireApiKeys) {
    $DoctorArgs += "--require-api-keys"
}

& $PythonExe @DoctorArgs
& $PythonExe -m pytest
