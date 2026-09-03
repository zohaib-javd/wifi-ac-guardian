<#
One-command Windows release build. It preserves all pre-existing checks and
uses a temporary short drive path only for the electron-builder target stage.
#>
param(
  [ValidateSet('all', 'portable', 'nsis')][string]$Target = 'all',
  [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$uiRoot = Join-Path $root 'wifi-guardian-ui'
$drive = 'W:'

function Invoke-Step([string]$Label, [scriptblock]$Action) {
  Write-Host "[WiFi AC Guardian] $Label" -ForegroundColor Cyan
  & $Action
  if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "$Label failed with exit code $LASTEXITCODE." }
}

Push-Location $root
try {
  Invoke-Step 'Running Windows backend tests' { py -m pytest tests -v }
  if (-not $SkipInstall) {
    Push-Location $uiRoot
    try { Invoke-Step 'Installing locked Electron dependencies' { npm ci } }
    finally { Pop-Location }
  }

  Push-Location $uiRoot
  try {
    Invoke-Step 'Building self-contained Guardian backend' { npm run build:guardian-backend }
    Invoke-Step 'Building static dashboard' { npm run build }
    Invoke-Step 'Running Electron release guards' {
      npm run verify:static-ui
      npm run verify:single-instance
      npm run verify:dashboard-states
      npm run verify:startup-readiness
      npm run verify:installer-shutdown
      npm run verify:backend-watchdog
    }
  }
  finally { Pop-Location }

  # subst.exe is called directly (not via "cmd /c" with a nested quoted
  # string) because cmd.exe does not understand backslash-escaped quotes:
  # a long $root containing spaces made the previous "cmd /c `"subst ... \`"$root\`"`"`"
  # form truncate the path at the first embedded \" and fail with
  # "Incorrect number of parameters". PowerShell quotes native-exe arguments
  # itself, so passing $root as its own argument avoids that entirely.
  & subst.exe $drive $root
  if ($LASTEXITCODE -ne 0) { throw "subst failed to map $drive to $root (exit code $LASTEXITCODE)." }
  try {
    Push-Location "$drive\wifi-guardian-ui"
    try {
      if ($Target -in @('all', 'portable')) { Invoke-Step 'Packaging portable executable' { npx electron-builder --win portable } }
      if ($Target -in @('all', 'nsis')) { Invoke-Step 'Packaging NSIS installer' { npx electron-builder --win nsis } }
    }
    finally { Pop-Location }
  }
  finally { & subst.exe $drive /D | Out-Null }

  Write-Host "[SUCCESS] Verified release artifacts are in $uiRoot\build_app" -ForegroundColor Green
}
finally { Pop-Location }
