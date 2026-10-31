# ==============================================================================
# git-release-bundler: 1-Click Installer
# ==============================================================================
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$currentDir = $PSScriptRoot
$skillsSourceDir = Join-Path $currentDir "skills"

if (-not (Test-Path $skillsSourceDir)) {
    Write-Error "[ERROR] Khong tim thay thu muc 'skills' trong thu muc hien tai."
    exit 1
}

$userHome = $HOME
if (-not $userHome) {
    $userHome = $env:USERPROFILE
}

$geminiSkillsDir = Join-Path $userHome ".gemini\config\skills"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Installing git-release-bundler..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Copy skills to ~/.gemini/config/skills/
$targetGitMark = Join-Path $geminiSkillsDir "git-mark"
$targetBundleLocal = Join-Path $geminiSkillsDir "bundle-local"

New-Item -ItemType Directory -Path $targetGitMark, $targetBundleLocal -Force | Out-Null

Copy-Item -Path (Join-Path $skillsSourceDir "git-mark\*") -Destination $targetGitMark -Recurse -Force
Copy-Item -Path (Join-Path $skillsSourceDir "bundle-local\*") -Destination $targetBundleLocal -Recurse -Force

Write-Host " [OK] Installed skills to: $geminiSkillsDir" -ForegroundColor Green

# 2. Configure Git Aliases globally
$markScript = (Join-Path $targetGitMark "scripts\mark.ps1").Replace('\', '/')
$bundleScript = (Join-Path $targetBundleLocal "scripts\bundle-local.ps1").Replace('\', '/')

$markCmd = "!powershell -NoProfile -ExecutionPolicy Bypass -File `"$markScript`""
$bundleCmd = "!f() { powershell -NoProfile -ExecutionPolicy Bypass -File `"$bundleScript`" -Version `"`$1`" -ModeOrBase `"`$2`"; }; f"

& git config --global alias.mark $markCmd
& git config --global alias.git-mark $markCmd
& git config --global alias.bundle-local $bundleCmd

Write-Host " [OK] Configured Git global aliases:" -ForegroundColor Green
Write-Host "      - git mark"
Write-Host "      - git git-mark"
Write-Host "      - git bundle-local"

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " SUCCESS! git-release-bundler da duoc cai dat thanh cong!" -ForegroundColor Green
Write-Host " Ban co the su dung ngay bay gio tren Terminal hoac AI Chat:" -ForegroundColor Green
Write-Host "   1. git mark              (hoac trong Chat: /git-mark)"
Write-Host "   2. git mark list         (hoac trong Chat: /git-mark list)"
Write-Host "   3. git bundle-local <ver>(hoac trong Chat: /bundle-local <ver>)"
Write-Host "==========================================================" -ForegroundColor Green
