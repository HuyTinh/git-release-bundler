# ==============================================================================
# git-release-bundler: 1-Click Installer (Windows PowerShell)
# ==============================================================================
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# 1. Verify Python installation
$pythonCmd = "python"
$null = Get-Command python -ErrorAction SilentlyContinue
if (-not $?) {
    $null = Get-Command py -ErrorAction SilentlyContinue
    if ($?) {
        $pythonCmd = "py"
    } else {
        Write-Error "[ERROR] Python is not installed or not found in PATH. Please install Python 3."
        exit 1
    }
}

$currentDir = $PSScriptRoot
$skillsSourceDir = Join-Path $currentDir "skills"

if (-not (Test-Path $skillsSourceDir)) {
    Write-Error "[ERROR] 'skills' directory not found in: $currentDir"
    exit 1
}

$userHome = $HOME
if (-not $userHome) {
    $userHome = $env:USERPROFILE
}

$geminiSkillsDir = Join-Path $userHome ".gemini\config\skills"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Installing git-release-bundler (Python Engine)..." -ForegroundColor Cyan
Write-Host " Detected Python command: $pythonCmd" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 2. Copy skills to ~/.gemini/config/skills/
$targetGitMark = Join-Path $geminiSkillsDir "git-mark"
$targetBundleLocal = Join-Path $geminiSkillsDir "bundle-local"

New-Item -ItemType Directory -Path $targetGitMark, $targetBundleLocal -Force | Out-Null

Copy-Item -Path (Join-Path $skillsSourceDir "git-mark\*") -Destination $targetGitMark -Recurse -Force
Copy-Item -Path (Join-Path $skillsSourceDir "bundle-local\*") -Destination $targetBundleLocal -Recurse -Force

Write-Host " [OK] Installed skills to: $geminiSkillsDir" -ForegroundColor Green

# 3. Configure Git Aliases globally using Python
$markScript = (Join-Path $targetGitMark "scripts\mark.py").Replace('\', '/')
$bundleScript = (Join-Path $targetBundleLocal "scripts\bundle_local.py").Replace('\', '/')

$markCmd = "!$pythonCmd `"$markScript`""
$bundleCmd = "!f() { $pythonCmd `"$bundleScript`" `"`$1`" `"`$2`"; }; f"

& git config --global alias.mark $markCmd
& git config --global alias.git-mark $markCmd
& git config --global alias.bundle-local $bundleCmd

Write-Host " [OK] Configured Git global aliases:" -ForegroundColor Green
Write-Host "      - git mark"
Write-Host "      - git git-mark"
Write-Host "      - git bundle-local"

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " SUCCESS! git-release-bundler installed successfully!" -ForegroundColor Green
Write-Host " You can now use it anywhere via Terminal or AI Chat:" -ForegroundColor Green
Write-Host "   1. git mark              (or in Chat: /git-mark)"
Write-Host "   2. git mark list         (or in Chat: /git-mark list)"
Write-Host "   3. git bundle-local <ver>(or in Chat: /bundle-local <ver>)"
Write-Host "==========================================================" -ForegroundColor Green
