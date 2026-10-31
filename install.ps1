# ==============================================================================
# git-release-bundler: 1-Click Installer (Windows PowerShell)
# ==============================================================================
[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# 1. Verify Python >= 3.8 (Item 4)
$pythonCmd = "python"
$null = Get-Command python -ErrorAction SilentlyContinue
if (-not $?) {
    $null = Get-Command py -ErrorAction SilentlyContinue
    if ($?) {
        $pythonCmd = "py"
    } else {
        Write-Error "[ERROR] Python 3 is not installed or not found in PATH."
        exit 1
    }
}

$pyCheckCode = "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"
$pyCheck = & $pythonCmd -c $pyCheckCode
if ($LASTEXITCODE -ne 0) {
    $verOut = & $pythonCmd --version
    Write-Error "[ERROR] Python >= 3.8 is required. Detected: $verOut"
    exit 1
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

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Installing git-release-bundler (Python Engine)..." -ForegroundColor Cyan
Write-Host " Detected Python command: $pythonCmd (>= 3.8)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 2. Deploy to Gemini / Antigravity skills (~/.gemini/config/skills)
$geminiSkillsDir = Join-Path $userHome ".gemini\config\skills"
$geminiGitMark = Join-Path $geminiSkillsDir "git-mark"
$geminiBundleLocal = Join-Path $geminiSkillsDir "bundle-local"

New-Item -ItemType Directory -Path $geminiGitMark, $geminiBundleLocal -Force | Out-Null
Copy-Item -Path (Join-Path $skillsSourceDir "git-mark\*") -Destination $geminiGitMark -Recurse -Force
Copy-Item -Path (Join-Path $skillsSourceDir "bundle-local\*") -Destination $geminiBundleLocal -Recurse -Force
Write-Host " [OK] Installed skills to Antigravity: $geminiSkillsDir" -ForegroundColor Green

# 3. Deploy to Claude Code skills (~/.claude/skills) if applicable (Item 9)
$claudeHomeDir = Join-Path $userHome ".claude"
if (Test-Path $claudeHomeDir) {
    $claudeSkillsDir = Join-Path $claudeHomeDir "skills"
    $claudeGitMark = Join-Path $claudeSkillsDir "git-mark"
    $claudeBundleLocal = Join-Path $claudeSkillsDir "bundle-local"

    New-Item -ItemType Directory -Path $claudeGitMark, $claudeBundleLocal -Force | Out-Null
    Copy-Item -Path (Join-Path $skillsSourceDir "git-mark\*") -Destination $claudeGitMark -Recurse -Force
    Copy-Item -Path (Join-Path $skillsSourceDir "bundle-local\*") -Destination $claudeBundleLocal -Recurse -Force
    Write-Host " [OK] Installed skills to Claude Code: $claudeSkillsDir" -ForegroundColor Green
}

# 4. Configure Git Aliases globally (Items 3, 4)
# Warning check for existing aliases
$existingMark = git config --global --get alias.mark 2>$null
$existingBundle = git config --global --get alias.bundle-local 2>$null

if ($existingMark -and -not $Force) {
    Write-Host "[WARN] Existing 'git mark' alias detected: $existingMark (Overwriting with new version)" -ForegroundColor Yellow
}
if ($existingBundle -and -not $Force) {
    Write-Host "[WARN] Existing 'git bundle-local' alias detected: $existingBundle (Overwriting with new version)" -ForegroundColor Yellow
}

# Remove redundant alias git-git-mark if present (Item 4)
& git config --global --unset-all alias.git-mark 2>$null

$markScript = (Join-Path $geminiGitMark "scripts\mark.py").Replace('\', '/')
$bundleScript = (Join-Path $geminiBundleLocal "scripts\bundle_local.py").Replace('\', '/')

# Item (3): Use "$@" in alias
$markCmd = "!f() { $pythonCmd `"$markScript`" `"`$@`"; }; f"
$bundleCmd = "!f() { $pythonCmd `"$bundleScript`" `"`$@`"; }; f"

& git config --global alias.mark $markCmd
& git config --global alias.bundle-local $bundleCmd

Write-Host " [OK] Configured Git global aliases:" -ForegroundColor Green
Write-Host "      - git mark"
Write-Host "      - git bundle-local"

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " SUCCESS! git-release-bundler installed successfully!" -ForegroundColor Green
Write-Host " You can now use it anywhere via Terminal or AI Chat:" -ForegroundColor Green
Write-Host "   1. git mark [branch]            (or in Chat: /git-mark)"
Write-Host "   2. git mark list                (or in Chat: /git-mark list)"
Write-Host "   3. git bundle-local <ver> [opt] (or in Chat: /bundle-local <ver>)"
Write-Host "==========================================================" -ForegroundColor Green
