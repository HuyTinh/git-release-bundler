# 📦 git-release-bundler

> **Universal Local Release Toolkit & AI Agent Skills for Git**  
> Mark branches, extract changes, compile combined database scripts, and generate 2-tier release notes — 100% locally with zero checkouts, zero remote clutter, and zero third-party dependencies.

[![CI](https://github.com/HuyTinh/git-release-bundler/actions/workflows/ci.yml/badge.svg)](https://github.com/HuyTinh/git-release-bundler/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-green.svg)](#)
[![Release](https://img.shields.io/github/v/release/HuyTinh/git-release-bundler)](https://github.com/HuyTinh/git-release-bundler/releases)

---

## 🌟 Why `git-release-bundler`? / Tại sao cần?

In modern software development (Agile / Sprint cycles), features and bugfixes are developed across multiple isolated branches (`feat/order`, `feat/payment`, `fix/auth`). When preparing a release candidate for UAT, Staging, or Deployment:
1. You have to remember which branches belong to this release.
2. You must manually hunt down SQL migration scripts (`*.sql`) across folders and concatenate them into one DB update script.
3. You have to compile clean release notes for PO, QA, and Clients without committing clutter or pushing premature Git tags.

**`git-release-bundler` provides a streamlined workflow to mark branches incrementally and compile complete release deliverables on demand.**

---

## ⚡ Key Capabilities / Tính năng nổi bật

- **100% Pure Local (Zero Remote Footprint)**: No git pushes, no git tags, no synthetic merge branches created on remote.
- **Zero-Checkout Engine (`git show`)**: Extracts commits and database scripts directly from Git's internal Object Database. Never touches your working tree, dirty files, or uncommitted work.
- **Industry Standard 2-Tier Changelog**:
  - **Tier 1 (Ready-to-copy)**: Strips technical commit prefixes (`feat:`, `fix(scope)!:`, Jira ticket IDs `[PROJ-123]`, `revert`) and deduplicates items into clean business-friendly bullet points for PO/QA/Stakeholders.
  - **Tier 2 (Technical Audit)**: Retains commit hashes `[%h]`, authors, and relative timestamps grouped by branch for developers.
- **Deterministic SQL Compilation & Collision Guard**:
  - Concatenates all `*.sql` files across any folder structure (`database/`, `migrations/`, `db/migration/`).
  - Strict alphabetical path sorting guarantees consistent execution order.
  - Content hashing (SHA-256) automatically deduplicates identical scripts and injects clear `[COLLISION WARNING]` alerts if branches introduce conflicting file contents.
  - Automatically filters out deleted files (`--diff-filter=ACMR`).
- **Working Tree Cleanliness**: Automatically appends `release_output/` to `.git/info/exclude`, keeping your working tree and `.gitignore` 100% untouched.
- **Smart Accumulate & Fresh Overwrite**: Missed a branch? Mark the additional branch and re-run with the same version name — it merges old and new branches into an updated bundle. Pass `--fresh` (or `-fresh`) to overwrite from scratch.
- **Cross-Platform & Cross-Agent**: Python 3.8+ Standard Library only (zero `pip install`). Compatible with **Antigravity**, **Claude Code**, **Cursor**, **Windsurf**, and standard **Terminal CLI**.

---

## 🚀 Installation / Cài đặt

### 1. Clone the repository
```bash
git clone https://github.com/HuyTinh/git-release-bundler.git
cd git-release-bundler
```

### 2. Run the 1-Click Installer

#### On Windows (PowerShell):
```powershell
./install.ps1
```

#### On macOS / Linux (Bash / Zsh):
```bash
chmod +x install.sh
./install.sh
```

The installer automatically:
1. Verifies Python >= 3.8 is available.
2. Deploys agent skills to `~/.gemini/config/skills/` (and `~/.claude/skills/` if Claude Code is installed).
3. Registers global Git aliases (`git mark`, `git bundle-local`) with safe argument forwarding (`"$@"`), warning if aliases already exist.

*(To cleanly uninstall anytime: `./uninstall.ps1` or `./uninstall.sh`)*

---

## 📖 Usage Guide / Hướng dẫn sử dụng

### 1. In Terminal (PowerShell / Git Bash / Zsh)

```bash
# 1. Mark the branch you just finished:
git mark

# Or mark a specific branch without checking it out:
git mark feat/order-service

# 2. View all currently marked branches:
git mark list

# 3. Unmark a branch if needed:
git mark unmark feat/order-service

# 4. Compile the release bundle:
git bundle-local uat-1.1.3

# Options:
# Recompile cleanly from scratch without merging previously bundled branches:
git bundle-local uat-1.1.3 --fresh

# Specify a custom base branch for diffing (default: develop or main):
git bundle-local uat-1.1.3 --base master
```

---

### 2. In AI Agent Chat (Antigravity / Claude Code)

| Chat Command | Description |
| :--- | :--- |
| `/git-mark` or `/mark` | Mark currently checked-out branch |
| `/git-mark <branch_name>` | Mark an explicit branch |
| `/git-mark list` | Display numbered list of marked branches |
| `/git-mark unmark <branch>` | Remove a branch from the list |
| `/git-mark clear` | Clear the marked list |
| `/bundle-local <version>` | Compile changelog & SQL scripts (e.g. `/bundle-local uat-1.1.3`) |
| `/bundle-local <version> --fresh` | Overwrite target release bundle from scratch |

---

## 🔍 Base Branch Diffing & Git Resolution

Understanding how `git-release-bundler` determines changes between branches:

### Base Branch Detection
- By default, the bundler inspects the repository for `develop` or `main` (in that order).
- You can override this using the `--base <branch>` / `-b <branch>` CLI option.

### Merge-Base Calculation
- Changes are computed using `git merge-base <base> <branch>`. Only commits and SQL file modifications made on the branch since diverging from the common ancestor are collected (`git log <merge-base>..<branch>` and `git diff <merge-base>..<branch>`).

### Squash-Merged Branches
- If a branch was already squash-merged into the base branch, `git log <merge-base>..<branch>` still correctly reflects individual commit messages from the local feature branch for documentation purposes. If the SQL files are identical to base, `git diff` produces an empty changeset as expected.

### Remote-Only Branches
- `git mark` operates on local Git references.
- If a branch only exists on remote (`origin/feat/xy`), create a local tracking branch first:
  ```bash
  git checkout --track origin/feat/xy
  # Or:
  git branch feat/xy origin/feat/xy
  ```
- If a marked branch cannot be resolved locally at bundling time, a warning is printed (`[WARN] Branch '<name>' could not be resolved locally. Skipping.`), and the tool continues processing remaining branches.

### Deleted Branches
- If a branch is deleted after being marked, it is gracefully skipped during bundling and automatically purged when the state file resets.

---

## 📂 State & Output Directory Structure

### State Storage
- Marked branches are stored in `.git/marked_branches.txt` inside your repository.
- This file is strictly repository-local, invisible to `git status`, and safely removed once `git bundle-local` finishes successfully.

### Output Structure
When a bundle is generated, output files are written to:
```text
# If the repo contains a .antigravity directory:
.antigravity/
└── release_output/
    └── uat-1.1.3/                      <-- Release version directory
        ├── branches.txt                <-- Source branches recorded
        ├── CHANGELOG_LOCAL.md          <-- 2-tier Changelog
        └── combined_db_scripts.sql     <-- Compiled SQL migrations

# Standard repository:
release_output/
└── uat-1.1.3/
    ├── branches.txt
    ├── CHANGELOG_LOCAL.md
    └── combined_db_scripts.sql
```

The output directory `release_output/` is automatically added to `.git/info/exclude` to guarantee zero uncommitted noise in your repository.

---

## 🤖 Cross-Agent Setup (Cursor / Windsurf / Claude Code)

- **Claude Code**: The installer automatically copies skills to `~/.claude/skills` if Claude Code exists.
- **Cursor / Windsurf**: Add the following instruction to `.cursorrules` or `.windsurfrules`:
  ```text
  When asked to bundle a release or when the user invokes /bundle-local <version>,
  execute the global Git alias:
    git bundle-local "<version>"
  Or execute directly via Python:
    python -m bundle_local "<version>"
  ```
- **Plain Terminal**: Execute `git mark` and `git bundle-local` in any terminal without AI tools.

---

## 🛠️ Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `[ERROR] Python 3.8 or higher is required` | Python version is older than 3.8 or not installed. | Upgrade Python to version 3.8 or newer and ensure `python` is added to your system `PATH`. |
| `[ERROR] No branches currently marked` | Attempted to bundle before marking branches. | Run `git mark` or `git mark <branch_name>` first. |
| `[SECURITY ERROR] Invalid version name` | Version name contains illegal characters, spaces, or traversal `..`. | Use alphanumeric characters, dots, dashes, and underscores only (e.g. `uat-1.1.3`, `v2.0.0-rc1`). |
| `[WARN] SQL file '...' has differing contents` | Multiple branches modified the same SQL script with different code. | Review the collision warning in `combined_db_scripts.sql` header and verify which branch version to keep. |
| `[WARN] Git alias 'mark' already exists` | An alias with the same name was configured earlier. | The installer will prompt or overwrite with the new alias definition. |
| Exit code 2 returned | Usage error or missing precondition (empty repo, no branches). | Check terminal output message for required action. |

---

## ⚠️ Limitations

1. **Local Branch Requirement**: Branches must be accessible as local Git references. Fetch remote branches before marking if needed.
2. **SQL Execution Ordering**: Scripts are ordered deterministically by file path. To ensure proper dependency order, use standard migration naming conventions (e.g., `V001__init.sql`, `V002__add_users.sql`).
3. **Git Repository Root**: Must be executed within a valid Git repository.

---

## 📄 License & Author
Released under the [MIT License](LICENSE).  
Author: [HuyTinh](https://github.com/HuyTinh)
