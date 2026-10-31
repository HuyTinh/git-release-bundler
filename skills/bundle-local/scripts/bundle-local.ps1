[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [string]$Version = "",
    [Parameter(Position=1)]
    [string]$ModeOrBase = "",
    [switch]$Fresh
)

$ErrorActionPreference = "Continue"

# Check if Fresh mode requested via positional argument or switch
$isFreshMode = $Fresh.IsPresent -or ($ModeOrBase -in @("-fresh", "--fresh", "-clean", "--clean"))
$customBase = if ($ModeOrBase -and -not $isFreshMode) { $ModeOrBase } else { "" }

# 1. Check if inside a Git repository
$gitRoot = (git rev-parse --show-toplevel 2>$null)
if (-not $gitRoot) {
    Write-Error "Not inside a git repository."
    exit 1
}
Set-Location $gitRoot

# 2. Check marked branches file
$gitDir = (git rev-parse --git-dir 2>$null)
$markedFile = Join-Path $gitRoot "$gitDir/marked_branches.txt"

if (-not (Test-Path $markedFile)) {
    Write-Warning "[WARN] Chua co nhanh nao duoc danh dau. Hay dung 'git mark' truoc."
    exit 0
}

$branches = @(Get-Content $markedFile | Where-Object { $_.Trim() -ne "" } | Select-Object -Unique)
if (-not $branches -or $branches.Count -eq 0) {
    Write-Warning "[WARN] Danh sach nhanh da mark dang trong."
    exit 0
}

# Check for uncommitted SQL files in working directory (excluding release_output and .antigravity)
$uncommittedSql = git status --porcelain "*.sql" 2>$null | Where-Object { 
    $_ -notmatch 'release_output' -and $_ -notmatch '\.antigravity' 
}
if ($uncommittedSql) {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Yellow
    Write-Host "[CANH BAO] Phat hien file SQL chua commit trong thu muc lam viec:" -ForegroundColor Yellow
    $uncommittedSql | ForEach-Object { Write-Host "   $_" -ForegroundColor Yellow }
    Write-Host "Luu y: Chi nhung file SQL DA COMMIT moi duoc trich xuat vao release bundle." -ForegroundColor Yellow
    Write-Host "==========================================================" -ForegroundColor Yellow
    Write-Host ""
}

# 3. Determine base branch (customBase -> develop -> dev -> main -> master)
$baseBranch = "develop"
if ($customBase) {
    git rev-parse --verify --quiet "$customBase" >$null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $baseBranch = $customBase
    } else {
        Write-Warning "[WARN] Khong tim thay nhanh base '$customBase', tu dong tim kiem base mac dinh..."
    }
}

if (-not $customBase -or $baseBranch -ne $customBase) {
    $candidateBases = @("develop", "dev", "main", "master")
    $found = $false
    foreach ($cand in $candidateBases) {
        git rev-parse --verify --quiet $cand >$null 2>&1
        if ($LASTEXITCODE -eq 0) {
            $baseBranch = $cand
            $found = $true
            break
        }
    }
    if (-not $found) {
        $baseBranch = (git branch --show-current)
    }
}

# 4. Sanitize version name
if (-not $Version -or $Version.Trim() -eq "") {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $Version = "release-$timestamp"
} else {
    $Version = $Version.Trim() -replace '[\\/:*?"<>|]', '-'
}

# 5. Determine output directory
$baseOutputDir = if (Test-Path (Join-Path $gitRoot ".antigravity")) {
    Join-Path $gitRoot ".antigravity/release_output"
} else {
    Join-Path $gitRoot "release_output"
}

$targetDir = Join-Path $baseOutputDir $Version
if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

# Ensure output directory is added to .gitignore if .gitignore exists
$gitignorePath = Join-Path $gitRoot ".gitignore"
$ignoreEntry = if (Test-Path (Join-Path $gitRoot ".antigravity")) { ".antigravity/release_output/" } else { "release_output/" }
if (Test-Path $gitignorePath) {
    $content = Get-Content $gitignorePath -Raw
    if ($content -notmatch [regex]::Escape($ignoreEntry)) {
        Add-Content -Path $gitignorePath -Value "`n$ignoreEntry"
    }
}

# 6. Save branches.txt (Smart Accumulate: If version folder already exists, merge with old branches unless -fresh)
$branchesFilePath = Join-Path $targetDir "branches.txt"
if ((Test-Path $branchesFilePath) -and -not $isFreshMode) {
    $oldBranches = @(Get-Content $branchesFilePath | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
    $newBranches = @($branches | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
    $mergedBranches = @($oldBranches + $newBranches) | Select-Object -Unique
    $newCount = $mergedBranches.Count - $oldBranches.Count
    Write-Host ""
    Write-Host "[CAP NHAT] Phien ban '$Version' da ton tai tu truoc!" -ForegroundColor Cyan
    Write-Host "-> Da hop nhat $($oldBranches.Count) nhanh cu + $newCount nhanh bo sung moi." -ForegroundColor Cyan
    Write-Host "-> Tong cong ban release gio day gom: $($mergedBranches.Count) nhanh." -ForegroundColor Cyan
    Write-Host ""
    $branches = $mergedBranches
} elseif ($isFreshMode -and (Test-Path $targetDir)) {
    Write-Host ""
    Write-Host "[FRESH] Che do lam moi: Tao lai hoan toan phien ban '$Version' voi $($branches.Count) nhanh moi." -ForegroundColor Yellow
    Write-Host ""
}

$branches | Set-Content -Path $branchesFilePath -Encoding utf8

# 7. Collect Commits (Changelog) & SQL files
$nowStr = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$changelogLines = @(
    "# Release Changelog: $Version",
    "- Thoi gian tao: $nowStr",
    "- Nhanh goc (Base): $baseBranch",
    "- So luong nhanh: $($branches.Count)",
    "",
    "### Danh sach tinh nang va thay doi (Ready-to-copy):"
)

$businessLines = @()
$branchCommitBlocks = @()
$sqlFilesMap = [System.Collections.Generic.Dictionary[string, System.Collections.Generic.List[string]]]::new()

foreach ($b in $branches) {
    git rev-parse --verify --quiet $b >$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        continue
    }

    $mergeBase = (git merge-base $baseBranch $b 2>$null)
    if (-not $mergeBase) {
        $mergeBase = $baseBranch
    }
    
    # 1. Business summary entries (Strip Jira ticket brackets and Conventional Commit prefixes)
    $commitEntries = git log "$mergeBase..$b" --no-merges --format="%s" 2>$null
    if ($commitEntries) {
        foreach ($cmsg in $commitEntries) {
            $cleanMsg = $cmsg -replace '^(\[[^\]]+\]\s*|[A-Z]+-\d+[:\s]+)?(feat|fix|chore|docs|refactor|update|style|perf|test|build|ci)(\([^\)]+\))?:\s*', ''
            if ($cleanMsg) {
                $cleanMsg = $cleanMsg.Substring(0,1).ToUpper() + $cleanMsg.Substring(1)
                $businessLines += "- $cleanMsg"
            }
        }
    }

    # 2. Technical detail entries
    $branchBlock = @()
    $branchBlock += "#### Nhanh: $b"
    $rawCommits = git log "$mergeBase..$b" --no-merges --format="- [%h] %s (%an, %cr)" 2>$null
    if ($rawCommits) {
        $branchBlock += $rawCommits
    } else {
        $branchBlock += "- *(Khong co commit moi so voi $baseBranch)*"
    }
    $branchBlock += ""
    $branchCommitBlocks += ($branchBlock -join "`n")
    
    # 3. SQL diff
    $sqlFiles = git diff --name-only --diff-filter=ACMR "$mergeBase..$b" -- "*.sql" 2>$null
    if ($sqlFiles) {
        foreach ($sql in $sqlFiles) {
            $cleanSql = $sql.Trim().Replace('\', '/')
            if (-not $sqlFilesMap.ContainsKey($cleanSql)) {
                $sqlFilesMap[$cleanSql] = [System.Collections.Generic.List[string]]::new()
            }
            if (-not $sqlFilesMap[$cleanSql].Contains($b)) {
                $sqlFilesMap[$cleanSql].Add($b)
            }
        }
    }
}

$uniqueBusiness = $businessLines | Select-Object -Unique
if ($uniqueBusiness) {
    $changelogLines += $uniqueBusiness
} else {
    $changelogLines += "- Khong co thay doi tinh nang nao."
}

$changelogLines += ""
$changelogLines += "---"
$changelogLines += "### Chi tiet Commits theo nhanh (Technical Audit):"
$changelogLines += ""
$changelogLines += ($branchCommitBlocks -join "`n")

# Write Changelog
$changelogPath = Join-Path $targetDir "CHANGELOG_LOCAL.md"
$changelogLines -join "`n" | Out-File -FilePath $changelogPath -Encoding utf8

# 8. Combine SQL files (Reading via git show without checkout)
$combinedSqlPath = Join-Path $targetDir "combined_db_scripts.sql"
$combinedSqlLines = @(
    "-- ======================================================================",
    "-- TONG HOP SCRIPT DATABASE: $Version",
    "-- Thoi gian tao: $nowStr",
    "-- Danh sach nhanh: $($branches -join ', ')",
    "-- ======================================================================",
    ""
)

if ($sqlFilesMap.Keys.Count -eq 0) {
    $combinedSqlLines += "-- [INFO] Khong co file SQL migration nao phat sinh trong cac nhanh nay.`n"
} else {
    $sortedFiles = $sqlFilesMap.Keys | Sort-Object
    foreach ($file in $sortedFiles) {
        $sourceBranch = $sqlFilesMap[$file][0]
        $otherBranches = if ($sqlFilesMap[$file].Count -gt 1) { " (Xuat hien ca o: " + ($sqlFilesMap[$file] -join ', ') + ")" } else { "" }
        
        $combinedSqlLines += "-- ----------------------------------------------------------------------"
        $combinedSqlLines += "-- FILE: $file"
        $combinedSqlLines += "-- NGUON TU NHANH: $sourceBranch$otherBranches"
        $combinedSqlLines += "-- ----------------------------------------------------------------------"
        
        $fileContent = git show "${sourceBranch}:${file}" 2>$null
        if ($fileContent) {
            $combinedSqlLines += $fileContent
            $combinedSqlLines += ""
        }
    }
}

$combinedSqlLines -join "`n" | Out-File -FilePath $combinedSqlPath -Encoding utf8

# 9. Clean up marked_branches.txt
Remove-Item -Path $markedFile -Force -ErrorAction SilentlyContinue

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] GOM BAN RELEASE LOCAL HOAN TAT: $Version" -ForegroundColor Green
Write-Host " Thu muc ket qua: $targetDir"
Write-Host "   1. Changelog:     $changelogPath"
Write-Host "   2. SQL tong hop:  $combinedSqlPath"
Write-Host "   3. Nguon nhanh:   $branchesFilePath"
Write-Host "==========================================================" -ForegroundColor Green
