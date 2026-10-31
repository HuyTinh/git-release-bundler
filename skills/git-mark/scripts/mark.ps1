[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [string]$ActionOrBranch = "",
    [Parameter(Position=1)]
    [string]$TargetBranch = ""
)

$ErrorActionPreference = "Continue"

# Check Git repository
$gitRoot = (git rev-parse --show-toplevel 2>$null)
if (-not $gitRoot) {
    Write-Host "[ERROR] Thu muc hien tai khong phai la mot Git repository." -ForegroundColor Red
    exit 1
}

$gitDir = (git rev-parse --git-dir 2>$null)
$markedFile = Join-Path $gitRoot "$gitDir/marked_branches.txt"

# 1. Handle 'list' action
if ($ActionOrBranch -in @("list", "-l", "--list")) {
    if (Test-Path $markedFile) {
        $branches = @(Get-Content $markedFile | Where-Object { $_.Trim() -ne "" })
        if ($branches -and $branches.Count -gt 0) {
            Write-Host "`nDanh sach cac nhanh dang cho gom ($($branches.Count) nhanh):" -ForegroundColor Cyan
            for ($i = 0; $i -lt $branches.Count; $i++) {
                Write-Host ("  {0,2}. {1}" -f ($i + 1), $branches[$i]) -ForegroundColor Green
            }
            Write-Host ""
        } else {
            Write-Host "Chua co nhanh nao duoc danh dau." -ForegroundColor Yellow
        }
    } else {
        Write-Host "Chua co nhanh nao duoc danh dau." -ForegroundColor Yellow
    }
    exit 0
}

# 2. Handle 'clear' action
if ($ActionOrBranch -in @("clear", "-c", "--clear")) {
    if (Test-Path $markedFile) {
        Remove-Item -Path $markedFile -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] Da xoa toan bo danh sach nhanh da danh dau." -ForegroundColor Green
    exit 0
}

# 3. Handle 'unmark' or 'rm' action
if ($ActionOrBranch -in @("unmark", "rm", "remove", "-d", "--delete")) {
    $branchToRemove = $TargetBranch
    if (-not $branchToRemove -or $branchToRemove.Trim() -eq "") {
        $branchToRemove = (git branch --show-current 2>$null)
    }
    $branchToRemove = $branchToRemove.Trim()
    
    if (Test-Path $markedFile) {
        $existing = @(Get-Content $markedFile | Where-Object { $_.Trim() -ne "" })
        if ($existing -contains $branchToRemove) {
            $updated = @($existing | Where-Object { $_ -ne $branchToRemove })
            if ($updated.Count -gt 0) {
                $updated | Set-Content -Path $markedFile -Encoding utf8
            } else {
                Remove-Item -Path $markedFile -Force -ErrorAction SilentlyContinue
            }
            Write-Host "[OK] Da go nhanh '$branchToRemove' khoi danh sach (Con lai: $($updated.Count) nhanh)." -ForegroundColor Green
        } else {
            Write-Host "[WARN] Nhanh '$branchToRemove' khong co trong danh sach danh dau." -ForegroundColor Yellow
        }
    } else {
        Write-Host "[WARN] Chua co nhanh nao duoc danh dau." -ForegroundColor Yellow
    }
    exit 0
}

# 4. Handle default 'mark' action
$branchToMark = $ActionOrBranch
if (-not $branchToMark -or $branchToMark.Trim() -eq "") {
    $branchToMark = (git branch --show-current 2>$null)
}

if (-not $branchToMark -or $branchToMark.Trim() -eq "") {
    Write-Host "[ERROR] Khong the xac dinh ten nhanh hien tai. Vui long chi dinh ten nhanh (VD: git mark feat/order)." -ForegroundColor Red
    exit 1
}

$branchToMark = $branchToMark.Trim()

# Check if branch exists in Git (warn if typo, skip check if it is the current checked-out branch)
$currentBranch = (git branch --show-current 2>$null)
if ($branchToMark -ne $currentBranch) {
    git rev-parse --verify --quiet "$branchToMark" >$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        git rev-parse --verify --quiet "origin/$branchToMark" >$null 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[CANH BAO] Khong tim thay nhanh '$branchToMark' trong Git local/remote. Hay kiem tra lai xem co go sai chinh ta khong." -ForegroundColor Yellow
        }
    }
}

$existing = @()
if (Test-Path $markedFile) {
    $existing = @(Get-Content $markedFile | Where-Object { $_.Trim() -ne "" })
}

if ($existing -contains $branchToMark) {
    Write-Host "[INFO] Nhanh '$branchToMark' da ton tai trong danh sach tu truoc ($($existing.Count) nhanh)." -ForegroundColor Yellow
} else {
    Add-Content -Path $markedFile -Value $branchToMark
    $count = $existing.Count + 1
    Write-Host "[OK] Da danh dau nhanh: $branchToMark (Tong cong: $count nhanh dang cho)." -ForegroundColor Green
}
