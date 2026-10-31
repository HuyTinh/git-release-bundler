# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-31

### Added
- **Core Engine (`bundle_local.py`)**:
  - Strict release version validation with regex `^[A-Za-z0-9][A-Za-z0-9._-]*$`, max 128 chars, prohibiting relative path traversal (`..`) and command injection.
  - Standardized exit codes: `0` for success, `1` for fatal/security errors, `2` for preconditions/empty repository.
  - Multi-encoding resilient Git file reader (`utf-8-sig`, `utf-16`, `latin-1`, `utf-8`) with explicit UTF-8 and LF output.
  - CLI argument parsing via `argparse` supporting `--fresh` and `-fresh` backward-compatible alias, as well as `--base` / `-b`.
  - Deterministic SQL script concatenation with alphabetical path sorting and SHA-256 collision detection across branches.
  - Automatic injection of `release_output/` into `.git/info/exclude` to keep working trees and `.gitignore` clean.
- **Branch Marker (`mark.py`)**:
  - Numbered listing of marked branches (`git mark list`).
  - Safe branch removal (`git mark unmark <branch>`) and list clearing (`git mark clear`).
  - UTF-8 file operations targeting `.git/marked_branches.txt`.
- **Installers & Uninstallers**:
  - PowerShell (`install.ps1`, `uninstall.ps1`) and Bash (`install.sh`, `uninstall.sh`) 1-click installers.
  - Python >= 3.8 preflight checks.
  - Warning on existing Git aliases before updating; safe argument forwarding using `"$@"`.
  - Automatic detection and deployment to Claude Code (`~/.claude/skills`) alongside Gemini/Antigravity (`~/.gemini/config/skills`).
- **Testing & CI/CD**:
  - Comprehensive unit test suite with `pytest` (`tests/test_bundler.py`) covering version validation, commit message cleaning (Conventional Commits, scopes, breaking changes, JIRA keys, reverts, Vietnamese unicode), and SQL collision detection.
  - GitHub Actions matrix workflow (`.github/workflows/ci.yml`) testing on Ubuntu, Windows, and macOS across Python 3.8–3.12.
- **Documentation**:
  - Full README with `git clone` steps, Base Branch diffing documentation, Troubleshooting matrix, and Limitations.
