# 📦 git-release-bundler

> **Universal Local Release Toolkit & AI Agent Skills for Git**  
> Mark branches, extract changes, compile combined database scripts with safety guards, and generate 4-section release notes — 100% locally with zero checkouts, zero remote clutter, and zero third-party dependencies.

[![CI](https://github.com/HuyTinh/git-release-bundler/actions/workflows/ci.yml/badge.svg)](https://github.com/HuyTinh/git-release-bundler/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/HuyTinh/git-release-bundler)](https://github.com/HuyTinh/git-release-bundler/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-green.svg)](#)

[📖 Đọc tài liệu Tiếng Việt (README.vi.md)](README.vi.md)

---

## 🌟 Why `git-release-bundler`?

In modern agile development, features and bugfixes are developed across multiple isolated branches (`feat/orders`, `fix/auth`, `feat/mobile-api`). When preparing a release candidate for QA, Staging, or Deployment:
1. You need to remember which branches belong to this release without merging them prematurely.
2. You must manually find and concatenate scattered `*.sql` database migrations in the correct order.
3. You need clean, executive-ready release notes for Stakeholders and distinct API endpoint lists for Frontend & Mobile teams.

**`git-release-bundler` automates this entire release preparation workflow locally in seconds with zero remote footprint.**

---

## ⚡ Key Capabilities

- **100% Pure Local (Zero Remote Footprint)**: No git pushes, no git tags, no temporary merge commits pushed to remote.
- **Zero-Checkout Extraction (`git show`)**: Reads commits and database scripts directly from Git's object database. Never touches your working tree, dirty files, or uncommitted work.
- **Standard 4-Section Changelog**:
  - **Section 1: Features & Business Highlights (Ready-to-copy)**: Categorized into `🚀 Features`, `🐛 Bug Fixes`, and `🔧 Other Improvements`, stripped of technical prefixes and trailers (`Co-authored-by`).
  - **Section 2: New API Endpoints (Web & Mobile)**: Flat, copyable bulleted list grouped by Web and Mobile.
  - **Section 3: Database Migrations**: List of compiled SQL files with SHA-256 checksums and safety notices.
  - **Section 4: Technical Audit**: Detailed commit hashes `[%h]`, authors, and relative timestamps grouped by branch.
- **SQL Safety & Collision Scanner**:
  - Automatically flags potentially destructive statements (`DROP TABLE/DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE`).
  - Strict alphabetical path sorting guarantees deterministic execution order.
  - SHA-256 hashing detects and alerts on cross-branch SQL file content collisions (`[COLLISION WARNING]`).
- **Reproducible Audit**: Records commit SHAs and generation timestamp in `branches.txt`.
- **Structured Metadata Export**: Produces `release_meta.json` for CI/CD or automated tooling.
- **Dry-Run Simulation**: `--dry-run` simulates the bundle without writing files to disk or clearing marked branches.
- **Cross-Platform & Cross-Agent**: Python 3.8+ Standard Library only (zero `pip install`). Compatible with **Antigravity**, **Claude Code**, **Cursor**, **Windsurf**, and standard terminal shells.

---

## 🚀 Quick Start & Installation

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

The installer verifies Python >= 3.8, deploys skills to `~/.gemini/config/skills/` (and `~/.claude/skills/` if Claude Code exists), and configures global Git aliases (`git mark`, `git bundle-local`).

*(To uninstall anytime: `./uninstall.ps1` or `./uninstall.sh`)*

---

## 📖 Usage Guide

### 1. In Terminal

```bash
# 1. Mark the branch you just finished:
git mark

# Or mark a specific branch without checking it out:
git mark feat/orders-export

# 2. View all currently marked branches:
git mark list

# 3. Unmark a branch if needed:
git mark unmark feat/orders-export

# 4. Clear the marked list completely:
git mark clear

# 5. Compile the release bundle:
git bundle-local uat-1.2.0

# Optional flags:
# Preview bundle without writing files or clearing marked list:
git bundle-local uat-1.2.0 --dry-run

# Overwrite target release bundle cleanly from scratch:
git bundle-local uat-1.2.0 --fresh

# Specify custom base branch (default: develop or main):
git bundle-local uat-1.2.0 --base staging
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
| `/bundle-local <version>` | Compile changelog & SQL scripts (e.g. `/bundle-local uat-1.2.0`) |
| `/bundle-local <version> --dry-run` | Preview without writing files |
| `/bundle-local <version> --fresh` | Overwrite target release bundle from scratch |

---

## 📂 Generated Release Output Structure

```text
release_output/
└── uat-1.2.0/
    ├── branches.txt                <-- Source branches with commit SHAs & timestamp
    ├── CHANGELOG_LOCAL.md          <-- 4-section changelog (Features, APIs, DB, Audit)
    ├── combined_db_scripts.sql     <-- Compiled SQL migrations with safety headers
    └── release_meta.json           <-- Machine-readable release metadata
```

*(If the project contains a `.antigravity` folder, the bundle is automatically placed in `.antigravity/release_output/` and excluded via `.git/info/exclude`)*.

👉 Check out the [examples/](examples/) directory to see real sample outputs!

---

## 🤖 Cursor Integration (.cursor/rules/)

For Cursor IDE users, copy `.cursor/rules/release-bundler.mdc` into your project's `.cursor/rules/` directory for automatic agent awareness.

---

## 🔒 Security & Limitations

### SQL Safety Scanner
`git-release-bundler` actively inspects SQL scripts for catastrophic commands (`DROP TABLE/DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE`). If found, it injects a high-visibility warning banner in `combined_db_scripts.sql` and logs an alert to stderr.

### Limitations
1. **Local Branch Availability**: Branches must be accessible as local Git references (run `git checkout --track origin/<branch>` if remote-only).
2. **Git Repository Root**: Must be executed inside a Git repository.
3. **No Automatic Database Execution**: This tool compiles scripts; it does not connect to or execute SQL against live databases.

---

## 🤝 Contributing & License

Contributions, bug reports, and pull requests are welcome!
To run tests locally:
```bash
pip install pytest
pytest tests/test_bundler.py -v
```

Released under the [MIT License](LICENSE).  
Author: [HuyTinh](https://github.com/HuyTinh)
