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
  - **Section 1: Features & Business Highlights (Ready-to-copy)**: User-facing, clean bullet points without technical prefixes (`feat:`, `fix(scope)!:`, `[TICKET-123]`, `revert`), automatically deduplicated for Stakeholders, QA, and PO.
  - **Section 2: New API Endpoints (Web & Mobile)**: Flat bulleted list of new endpoints (`METHOD /path` - description) grouped by **Web** and **Mobile**, optimized for 1-click copying.
  - **Section 3: Database Migrations**: Summary of concatenated SQL migration scripts.
  - **Section 4: Technical Audit**: Detailed commit audit logs (`[%h]`) grouped by branch for developers.
- **Deterministic SQL Compilation**: Alphabetical file sorting, SHA-256 deduplication, and collision detection warnings (`[COLLISION WARNING]`).
- **Output Precedence**:
  - If `.antigravity/` exists $\rightarrow$ output to `.antigravity/release_output/<version>/`
  - Otherwise $\rightarrow$ output to `release_output/<version>/`
- **Working Tree Cleanliness**: Output folder is automatically ignored via `.git/info/exclude`.

## Smart Capabilities
- **Smart Accumulate (Default)**: If the target version directory already exists, automatically merge newly marked branches with previous branches to regenerate a complete release bundle.
- **Fresh Overwrite Mode (`--fresh` or `-fresh`)**: Recreate the version from scratch using only newly marked branches: `/bundle-local <version> --fresh`.
- **Auto Base Detection**: Dynamically inspects `develop` $\rightarrow$ `dev` $\rightarrow$ `main` $\rightarrow$ `master` (or accept custom base: `/bundle-local <version> --base <branch>` or positional `<branch>`).
- **API Endpoint Detection**:
  - Recognizes commits like `feat(api-web): POST /api/v1/orders/export - Description` or `api(mobile): GET /api/v1/notifications`.
- **Deleted File Guard (`--diff-filter=ACMR`)**: Excludes deleted or renamed SQL migration files.

## Execution Directives
When invoked:
1. Execute the release bundler using the registered global Git alias:
   ```bash
   git bundle-local "<version>" [options]
   ```
   *(Or direct script execution: `python "<path>/bundle_local.py" "<version>" [options]`)*
2. Read the generated `CHANGELOG_LOCAL.md`:
   - Extract **Section 1 (Features & Business Highlights)** and **Section 2 (New API Endpoints)**, presenting them directly in chat formatted cleanly for 1-click copying.
   - If git diff has new Controller/Route definitions that were not tagged in commit messages, proactively surface them in the chat response.
   - Surface the path to `combined_db_scripts.sql` and note any `[COLLISION WARNING]` if present.
