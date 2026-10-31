# ==============================================================================
# git-release-bundler: 1-Click Uninstaller
# ==============================================================================
[CmdletBinding()]
param()

$userHome = $HOME
if (-not $userHome) {
    $userHome = $env:USERPROFILE
}

$geminiSkillsDir = Join-Path $userHome ".gemini\config\skills"

Write-Host "==========================================================" -ForegroundColor Yellow
Write-Host " Uninstalling git-release-bundler..." -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Yellow

# 1. Remove skills from ~/.gemini/config/skills/
$targetGitMark = Join-Path $geminiSkillsDir "git-mark"
$targetBundleLocal = Join-Path $geminiSkillsDir "bundle-local"

if (Test-Path $targetGitMark) {
    Remove-Item -Path $targetGitMark -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host " [OK] Removed: $targetGitMark" -ForegroundColor Green
}

if (Test-Path $targetBundleLocal) {
    Remove-Item -Path $targetBundleLocal -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host " [OK] Removed: $targetBundleLocal" -ForegroundColor Green
}

# 2. Remove Git Aliases
& git config --global --unset-all alias.mark 2>$null
& git config --global --unset-all alias.git-mark 2>$null
& git config --global --unset-all alias.bundle-local 2>$null

Write-Host " [OK] Removed Git global aliases." -ForegroundColor Green
Write-Host "`n[SUCCESS] Go cai dat hoan tat!" -ForegroundColor Green
