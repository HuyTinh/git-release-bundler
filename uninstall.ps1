# ==============================================================================
# git-release-bundler: 1-Click Uninstaller (Windows PowerShell)
# ==============================================================================
[CmdletBinding()]
param()

$userHome = $HOME
if (-not $userHome) {
    $userHome = $env:USERPROFILE
}

Write-Host "==========================================================" -ForegroundColor Yellow
Write-Host " Uninstalling git-release-bundler..." -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Yellow

# 1. Remove skills from Gemini / Antigravity
$geminiSkillsDir = Join-Path $userHome ".gemini\config\skills"
$geminiGitMark = Join-Path $geminiSkillsDir "git-mark"
$geminiBundleLocal = Join-Path $geminiSkillsDir "bundle-local"

if (Test-Path $geminiGitMark) {
    Remove-Item -Path $geminiGitMark -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host " [OK] Removed: $geminiGitMark" -ForegroundColor Green
}
if (Test-Path $geminiBundleLocal) {
    Remove-Item -Path $geminiBundleLocal -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host " [OK] Removed: $geminiBundleLocal" -ForegroundColor Green
}

# 2. Remove skills from Claude Code if present
$claudeSkillsDir = Join-Path $userHome ".claude\skills"
$claudeGitMark = Join-Path $claudeSkillsDir "git-mark"
$claudeBundleLocal = Join-Path $claudeSkillsDir "bundle-local"

if (Test-Path $claudeGitMark) {
    Remove-Item -Path $claudeGitMark -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host " [OK] Removed: $claudeGitMark" -ForegroundColor Green
}
if (Test-Path $claudeBundleLocal) {
    Remove-Item -Path $claudeBundleLocal -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host " [OK] Removed: $claudeBundleLocal" -ForegroundColor Green
}

# 3. Remove Git Aliases
& git config --global --unset-all alias.mark 2>$null
& git config --global --unset-all alias.git-mark 2>$null
& git config --global --unset-all alias.bundle-local 2>$null

Write-Host " [OK] Removed Git global aliases." -ForegroundColor Green
Write-Host "`n[SUCCESS] Uninstallation completed!" -ForegroundColor Green
