---
name: bundle-local
description: Consolidate local Git branch commits into a 2-tier changelog and compile DB migration SQL scripts into a single release bundle (.antigravity/release_output/<version>/ or release_output/<version>/). Triggered when user asks to bundle branches, compile release scripts, generate release changelog, or types /bundle-local <version>, "gom nhánh", "tạo release local".
---

# Bundle Local Release Skill

Automate local release compilation from marked Git branches (.git/marked_branches.txt).

## Core Directives
- **100% Local**: Never interact with remotes, never create tags, never create unnecessary merge branches, never push.
- **Zero-Checkout**: Extract SQL and commits via `git show` directly from the Git object database without altering the user's working tree or uncommitted files.
- **Standard 4-Section Changelog Structure**:
  - **Section 1: Features & Business Highlights (Ready-to-copy)**: Categorized into `🚀 Features`, `🐛 Bug Fixes`, and `🔧 Other Improvements`, automatically deduplicated and stripped of git trailers.
  - **Section 2: New API Endpoints (Web & Mobile)**: Flat bulleted list of new endpoints (`METHOD /path` - description) grouped by **Web** and **Mobile**, optimized for 1-click copying.
  - **Section 3: Database Migrations**: Summary of concatenated SQL migration scripts with SHA-256 checksums and safety warning summaries.
  - **Section 4: Technical Audit**: Detailed commit audit logs (`[%h]`) grouped by branch for developers.
- **SQL Safety & Collision Scanner**: Scans for `DROP`, `TRUNCATE`, and unconditioned `DELETE` statements, warning if detected, alongside SHA-256 collision detection.
- **Structured Metadata Export**: Automatically generates `release_meta.json` with machine-readable release information.
- **Output Precedence**:
  - If `.antigravity/` exists $\rightarrow$ output to `.antigravity/release_output/<version>/`
  - Otherwise $\rightarrow$ output to `release_output/<version>/`
- **Working Tree Cleanliness**: Output folder is automatically ignored via `.git/info/exclude`.

## Smart Capabilities
- **Smart Accumulate (Default)**: If the target version directory already exists, automatically merge newly marked branches with previous branches to regenerate a complete release bundle.
- **Fresh Overwrite Mode (`--fresh`)**: Recreate the version from scratch using only newly marked branches: `/bundle-local <version> --fresh`.
- **Dry Run Simulation (`--dry-run`)**: Preview the changelog and SQL scripts without writing files or clearing marked branches: `/bundle-local <version> --dry-run`.
- **Auto Base Detection**: Dynamically inspects `develop` $\rightarrow$ `dev` $\rightarrow$ `main` $\rightarrow$ `master` (or accept custom base: `/bundle-local <version> --base <branch>` or positional `<branch>`).
- **Deleted & Merged Branch Guards**: Automatically detects if marked branches were deleted locally or already merged into the base branch.

## Execution Directives
When invoked:
1. Execute the release bundler using the registered global Git alias:
   ```bash
   git bundle-local "<version>" [options]
   ```
   *(Or direct script execution: `python "<path>/bundle_local.py" "<version>" [options]`)*
2. Read the generated `CHANGELOG_LOCAL.md`:
   - Extract **Section 1 (Features & Highlights)** and **Section 2 (New API Endpoints)**, presenting them directly in chat formatted cleanly for 1-click copying.
   - If git diff has new Controller/Route definitions that were not tagged in commit messages, proactively surface them in the chat response.
   - Surface the path to `combined_db_scripts.sql` and highlight any `[CRITICAL SECURITY WARNING]` or `[COLLISION WARNING]` alerts.
