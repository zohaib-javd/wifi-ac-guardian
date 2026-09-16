<#
Build a self-contained Guardian backend for the Electron Windows release.

This intentionally produces a one-file PyInstaller bundle. The executable
extracts runtime DLLs under Windows' short temporary path, avoiding the Windows
MAX_PATH failure that occurs when a one-directory bundle sits below Electron's
long resources path.
#>
param(
  [switch]$Clean
)

$ErrorActionPreference = 'Stop'
$uiRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent $uiRoot
$sourcePackage = Join-Path $projectRoot 'wifi_ac_guardian_win'
$distRoot = Join-Path $uiRoot 'build_backend'
$workRoot = Join-Path $projectRoot '.cache\pyinstaller-work'
$specRoot = Join-Path $projectRoot '.cache\pyinstaller-spec'

if (-not (Test-Path (Join-Path $sourcePackage '__main__.py'))) {
  throw "Guardian source package is missing: $sourcePackage"
}

if ($Clean) {
  Remove-Item -Recurse -Force $distRoot, $workRoot, $specRoot -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Force $distRoot, $workRoot, $specRoot | Out-Null

$entryPoint = Join-Path $sourcePackage '__main__.py'
$assets = Join-Path $sourcePackage 'assets'

& py -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --name guardian-backend `
  --distpath $distRoot `
  --workpath $workRoot `
  --specpath $specRoot `
  --paths $projectRoot `
  --add-data "$assets;wifi_ac_guardian_win/assets" `
  --collect-submodules wifi_ac_guardian_win `
  --hidden-import wifi_ac_guardian_win.ipc_server `
  $entryPoint

if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller failed with exit code $LASTEXITCODE."
}

$backendExe = Join-Path $distRoot 'guardian-backend.exe'
if (-not (Test-Path $backendExe)) {
  throw "PyInstaller did not create the expected backend executable: $backendExe"
}

Write-Output "Built self-contained Guardian backend: $backendExe"
