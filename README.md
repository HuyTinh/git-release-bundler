# 📦 git-release-bundler

> **Universal Local Release Toolkit & AI Agent Skills for Git**  
> Mark branches, extract changes, compile combined database scripts, and generate 2-tier release notes — 100% locally with zero checkouts, zero remote clutter, and zero third-party dependencies.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-green.svg)](#)

---

## 🌟 Why `git-release-bundler`? / Tại sao cần?

In modern software development (Agile / Sprint cycles), features and bugfixes are developed across multiple isolated branches (`feat/order`, `feat/payment`, `fix/auth`). When preparing a release candidate for UAT, Staging, or Deployment:
1. You have to remember which branches belong to this release.
2. You must manually hunt down SQL migration scripts (`*.sql`) across folders and concatenate them into one DB update script.
3. You have to compile clean release notes for PO, QA, and Clients without committing clutter or pushing premature Git tags.

**`git-release-bundler` automates this entire preparation workflow locally with 2 simple commands!**

---

## ⚡ Key Capabilities / Tính năng nổi bật

- **100% Pure Local (Zero Remote Footprint)**: No git pushes, no git tags, no synthetic merge branches created on remote.
- **Zero-Checkout Engine (`git show`)**: Extracts commits and database scripts directly from Git's internal Object Database. Never touches your working tree, dirty files, or uncommitted work.
- **Industry Standard 2-Tier Changelog**:
  - **Tier 1 (Ready-to-copy)**: Strips technical commit prefixes (`feat:`, `fix:`, Jira ticket IDs `[PROJ-123]`) and deduplicates items into clean business-friendly bullet points for PO/QA/Stakeholders.
  - **Tier 2 (Technical Audit)**: Retains commit hashes `[%h]`, authors, and relative timestamps grouped by branch for developers.
- **Recursive Database Script Compilation**: Combines all `*.sql` files across any folder structure (`database/`, `migrations/`, `db/migration/`), with clear branch source headers and automatic exclusion of deleted files (`--diff-filter=ACMR`).
- **Smart Accumulate**: Missed a branch? Just mark the additional branch and re-run the same version name — it automatically merges old and new branches into an updated bundle. Use `-fresh` if you want to overwrite from scratch.
- **Cross-Platform & Cross-Agent**: Python 3 Standard Library only (zero `pip install`). Compatible with **Antigravity**, **Claude Code**, **Cursor**, **Windsurf**, and standard **Terminal CLI**.

---

## 🚀 1-Click Installation / Cài đặt nhanh

### On Windows (PowerShell):
```powershell
./install.ps1
```

### On macOS / Linux (Bash / Zsh):
```bash
chmod +x install.sh
./install.sh
```

The installer automatically:
1. Deploys skills to `~/.gemini/config/skills/`.
2. Registers global Git aliases (`git mark`, `git git-mark`, `git bundle-local`).

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

# (Optional: Recompile cleanly without merging previous branches)
git bundle-local uat-1.1.3 -fresh
```

---

### 2. In AI Agent Chat (Antigravity / Gemini CLI)

| Chat Command | Description |
| :--- | :--- |
| `/git-mark` or `/mark` | Mark currently checked-out branch |
| `/git-mark <branch_name>` | Mark an explicit branch |
| `/git-mark list` | Display numbered list of marked branches |
| `/git-mark unmark <branch>` | Remove a branch from the list |
| `/git-mark clear` | Clear the marked list |
| `/bundle-local <version>` | Compile changelog & SQL scripts (e.g. `/bundle-local uat-1.1.3`) |

---

## 📂 Generated Release Output Structure

```text
# If the repo contains a .antigravity directory:
.antigravity/
└── release_output/
    └── uat-1.1.3/                      <-- Your release version name
        ├── branches.txt                <-- List of source branches
        ├── CHANGELOG_LOCAL.md          <-- 2-tier Changelog (Ready-to-copy & Audit)
        └── combined_db_scripts.sql     <-- Compiled SQL migrations

# Standard repository:
release_output/
└── uat-1.1.3/
    ├── branches.txt
    ├── CHANGELOG_LOCAL.md
    └── combined_db_scripts.sql
```

---

## 🤖 Cross-Agent Setup (Claude Code / Cursor / Windsurf)

- **Claude Code**: Copy `skills/*` into `~/.claude/skills/`.
- **Cursor / Windsurf**: Add to `.cursorrules`:
  ```text
  When I ask to bundle a release or type /bundle-local <version>, execute:
  python "$HOME/.gemini/config/skills/bundle-local/scripts/bundle_local.py" "<version>"
  ```
- **Plain Terminal**: Use `git mark` and `git bundle-local` natively without any AI assistant.

---

## 📄 License
Released under the [MIT License](LICENSE).  
Author: [HuyTinh](https://github.com/HuyTinh).
