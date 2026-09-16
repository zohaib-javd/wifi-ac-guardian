param(
  [Parameter(Mandatory = $true)][ValidatePattern('^\d+\.\d+\.\d+$')][string]$Version
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$uiRoot = Join-Path $root 'wifi-guardian-ui'

function Set-Utf8NoBom([string]$Path, [string]$Value) {
  [System.IO.File]::WriteAllText($Path, $Value, [System.Text.UTF8Encoding]::new($false))
}

function Replace-One([string]$Path, [string]$Pattern, [string]$Replacement) {
  $content = Get-Content -Raw -LiteralPath $Path
  if (-not [regex]::IsMatch($content, $Pattern)) { throw "Version pattern not found in $Path" }
  $updated = [regex]::new($Pattern).Replace($content, $Replacement, 1)
  Set-Utf8NoBom $Path $updated
}

Set-Utf8NoBom (Join-Path $root 'VERSION') $Version
Replace-One (Join-Path $uiRoot 'package.json') '"version"\s*:\s*"[^"]+"' ('"version": "' + $Version + '"')

$lockPath = Join-Path $uiRoot 'package-lock.json'
if (Test-Path $lockPath) {
  Replace-One $lockPath '"version"\s*:\s*"[^"]+"' ('"version": "' + $Version + '"')
}

Replace-One (Join-Path $root 'wifi_ac_guardian_win\__init__.py') '__version__\s*=\s*"[^"]+"' ('__version__ = "' + $Version + '"')
Replace-One (Join-Path $root 'pyproject.toml') '(?m)^version\s*=\s*"[^"]+"' ('version = "' + $Version + '"')
Replace-One (Join-Path $root 'setup.py') 'version\s*=\s*"[^"]+"' ('version="' + $Version + '"')
Replace-One (Join-Path $uiRoot 'src\lib\release.ts') "RELEASE_VERSION = '[^']+'" ("RELEASE_VERSION = '$Version'")

$releaseJson = @{ version = $Version; publisher = 'Zohaib Javed (Zeejay)'; productName = 'WiFi AC Guardian' } | ConvertTo-Json
Set-Utf8NoBom (Join-Path $uiRoot 'public\release.json') $releaseJson

Push-Location $uiRoot
try {
  node scripts/verify-version-consistency.js
  if ($LASTEXITCODE -ne 0) { throw 'Version consistency verification failed.' }
} finally { Pop-Location }

Write-Host "[SUCCESS] WiFi AC Guardian release version synchronized to v$Version" -ForegroundColor Green
