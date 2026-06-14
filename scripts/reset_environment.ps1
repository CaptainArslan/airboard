# AirBoard - reset local caches and exported data (fresh start)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "AirBoard reset - clearing caches and old data..."

Get-ChildItem -Path (Join-Path $Root "src") -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    ForEach-Object {
        Write-Host "  remove $($_.FullName)"
        Remove-Item $_.FullName -Recurse -Force
    }

$exports = Join-Path $Root "exports"
if (Test-Path $exports) {
    Get-ChildItem $exports -Filter "*.png" -File -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "  remove export $($_.Name)"
        Remove-Item $_.FullName -Force
    }
}

Write-Host "Done. Restart the app for an empty canvas (state is in-memory only)."
