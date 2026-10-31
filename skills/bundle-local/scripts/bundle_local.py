#!/usr/bin/env python3
"""
git-bundle-local: Consolidate marked Git branches into a versioned local release bundle.
Generates 2-tier CHANGELOG_LOCAL.md and combined_db_scripts.sql.
Zero dependencies (Standard Library only). Cross-platform (Windows, macOS, Linux).
"""

from __future__ import annotations

import sys
import os
import re
import json
import datetime
import hashlib
import argparse
import subprocess
from pathlib import Path


def run_git(args: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return proc.returncode, proc.stdout.strip()
    except Exception as e:
        return 1, str(e)


def read_git_file(branch: str, file_path: str) -> str:
    """Read file content safely handling UTF-8, UTF-8-BOM, UTF-16 (SSMS/PowerShell), and Latin-1."""
    try:
        proc = subprocess.run(
            ["git", "show", f"{branch}:{file_path}"],
            capture_output=True
        )
        if proc.returncode != 0:
            return ""
        raw = proc.stdout
        for enc in ["utf-8-sig", "utf-16", "latin-1"]:
            try:
                return raw.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def clean_commit_message(msg: str) -> str:
    """
    Strips Conventional Commits (including breaking '!', scopes), Jira/Ticket IDs,
    and revert prefixes to produce a clean user-facing summary.
    """
    text = msg.strip()
    if not text:
        return ""

    # Strip Git trailers (Co-authored-by, Signed-off-by, Reviewed-by)
    text = re.sub(r'^(?:co-authored-by|signed-off-by|reviewed-by):.*$', '', text, flags=re.IGNORECASE | re.MULTILINE).strip()

    # Strip revert prefix: revert: "..." or Revert "..."
    text = re.sub(r'^(?:revert:\s*"?|Revert\s+"?)(.*?)"?$', r'\1', text, flags=re.IGNORECASE).strip()

    # Regex matches:
    # 1. Optional Ticket IDs like [PROJ-123], PROJ-123:, (#123)
    # 2. Conventional commit types: feat, fix, chore, docs, refactor, update, style, perf, test, build, ci
    # 3. Optional scope: (scope)
    # 4. Optional breaking change indicator: !
    # 5. Colon and trailing whitespace
    pattern = (
        r'^(?:\[[A-Za-z0-9_\-]+\]|\b[A-Za-z0-9_\-]+-\d+:|\(#[0-9]+\))\s*'
        r'|(?:\[[A-Za-z0-9_\-]+\]\s*)?'
        r'(?:feat|fix|hotfix|add|chore|docs|refactor|update|style|perf|test|build|ci|revert)'
        r'(?:\([^\)]+\))?!?:'
        r'\s*'
    )

    clean = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
    if clean:
        clean = clean[0].upper() + clean[1:]
    return clean if clean else text


def categorize_commit(msg: str) -> tuple[str, str]:
    """
    Categorizes commit into 'features', 'fixes', or 'others',
    and returns (category, cleaned_message).
    Filters git trailers like Co-authored-by.
    """
    text = msg.strip()
    text = re.sub(r'^(?:co-authored-by|signed-off-by|reviewed-by):.*$', '', text, flags=re.IGNORECASE | re.MULTILINE).strip()
    if not text:
        return "others", ""

    lower = text.lower()
    # Check if commit message indicates a feature
    if re.search(r'^(?:\[[A-Za-z0-9_\-]+\]\s*)?(?:[A-Za-z0-9_\-]+-\d+:\s*)?(?:feat|add)\b', lower):
        category = "features"
    # Check if commit message indicates a bugfix
    elif re.search(r'^(?:\[[A-Za-z0-9_\-]+\]\s*)?(?:[A-Za-z0-9_\-]+-\d+:\s*)?(?:fix|hotfix|bugfix|patch)\b', lower):
        category = "fixes"
    else:
        category = "others"

    clean = clean_commit_message(text)
    return category, clean


def scan_sql_safety(sql_text: str) -> list[str]:
    """
    Item (3): Scans SQL script for potentially destructive operations:
    - DROP TABLE / DATABASE / SCHEMA / VIEW
    - TRUNCATE TABLE
    - DELETE FROM without a WHERE clause
    Ignores SQL comments (-- and /* */).
    """
    warnings = []
    # Strip block comments /* ... */
    no_comments = re.sub(r'/\*.*?\*/', ' ', sql_text, flags=re.DOTALL)
    # Strip line comments -- ...
    no_comments = re.sub(r'--.*$', ' ', no_comments, flags=re.MULTILINE)

    # Split statements by semicolon
    statements = [s.strip() for s in no_comments.split(';') if s.strip()]

    for stmt in statements:
        # Check for DROP
        drop_match = re.search(r'\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW)\s+(?:IF\s+EXISTS\s+)?([`"\'\w\.]+)', stmt, re.IGNORECASE)
        if drop_match:
            warnings.append(f"Dangerous operation: DROP {drop_match.group(1).upper()} `{drop_match.group(2)}`")

        # Check for TRUNCATE
        trunc_match = re.search(r'\bTRUNCATE\s+(?:TABLE\s+)?([`"\'\w\.]+)', stmt, re.IGNORECASE)
        if trunc_match:
            warnings.append(f"Dangerous operation: TRUNCATE TABLE `{trunc_match.group(1)}`")

        # Check for DELETE without WHERE
        delete_match = re.search(r'\bDELETE\s+FROM\s+([`"\'\w\.]+)', stmt, re.IGNORECASE)
        if delete_match:
            if not re.search(r'\bWHERE\b', stmt, re.IGNORECASE):
                warnings.append(f"HIGH SEVERITY DANGER: DELETE FROM `{delete_match.group(1)}` without WHERE clause")

    return list(dict.fromkeys(warnings))


def validate_version_name(version: str) -> bool:
    """
    Item (1): Strict validation to prevent path traversal and injection.
    Only allows alphanumeric characters, dots, underscores, and dashes.
    Must start with alphanumeric to prevent '..' or '-rf'.
    """
    if not version or len(version) > 128:
        return False
    # Must start with letter or digit, followed by [A-Za-z0-9._-]
    if not re.match(r'^[A-Za-z0-9][A-Za-z0-9._-]*$', version):
        return False
    # Explicitly disallow any relative path traversal sequence
    if ".." in version:
        return False
    return True


API_COMMIT_PATTERN = re.compile(
    r'^(?:\[[A-Za-z0-9_\-]+\]\s*)?'
    r'(?:[A-Za-z0-9_\-]+-\d+:\s*)?'
    r'(?:feat|add|update|fix|api)?'
    r'\(.*?(web|mob|mobile).*?\)!?:\s*'
    r'([A-Z]+)\s+([/\w\-{}\.]+)'
    r'(?:\s*[-:]\s*(.*))?$',
    re.IGNORECASE
)


def extract_api_endpoint(msg: str) -> tuple[str, str] | None:
    """
    Extracts API method, path, and description from conventional commit messages.
    Returns (platform, formatted_line) where platform is 'web' or 'mobile'.
    Examples:
      feat(api-web): POST /api/v1/orders/export-excel - Xuất báo cáo đơn hàng ra Excel
        -> ("web", "`POST /api/v1/orders/export-excel` - Xuất báo cáo đơn hàng ra Excel")
      api(mobile): GET /api/v1/notifications
        -> ("mobile", "`GET /api/v1/notifications`")
    """
    m = API_COMMIT_PATTERN.match(msg.strip())
    if not m:
        return None
    raw_plat, method, path, desc = m.groups()
    platform = "mobile" if "mob" in raw_plat.lower() else "web"
    method_upper = method.upper()
    formatted = f"`{method_upper} {path}`"
    if desc and desc.strip():
        formatted += f" - {desc.strip()}"
    return platform, formatted


def format_changelog(
    version: str,
    base_branch: str,
    branches: list[str],
    now_str: str,
    features: list[str] = None,
    fixes: list[str] = None,
    others: list[str] = None,
    api_web_lines: list[str] = None,
    api_mob_lines: list[str] = None,
    sql_files: list[str] = None,
    branch_commit_blocks: list[str] = None,
    business_lines: list[str] = None,
) -> str:
    """
    Builds the standardized 4-section CHANGELOG_LOCAL.md:
      1. Features & Business Highlights (Ready-to-copy): Grouped into Features, Fixes, Others
      2. New API Endpoints (Web & Mobile)
      3. Database Migrations
      4. Technical Audit (Commits by branch)
    """
    lines = [
        f"# Release Changelog: {version}",
        f"- **Created at:** {now_str}",
        f"- **Base branch:** `{base_branch}`",
        f"- **Branch count:** {len(branches)}",
        "",
        "---",
        "",
        "### 1. Features & Business Highlights (Ready-to-copy):"
    ]

    # Backward compatibility if business_lines was provided
    if features is None and business_lines is not None:
        features = []
        fixes = []
        others = []
        for line in business_lines:
            raw_content = line.lstrip("- ").strip()
            cat, clean = categorize_commit(raw_content)
            if cat == "features":
                features.append(clean)
            elif cat == "fixes":
                fixes.append(clean)
            else:
                others.append(clean)

    unique_features = list(dict.fromkeys(features or []))
    unique_fixes = list(dict.fromkeys(fixes or []))
    unique_others = list(dict.fromkeys(others or []))

    has_entries = False
    if unique_features:
        lines.append("")
        lines.append("#### 🚀 Features:")
        for item in unique_features:
            lines.append(f"- {item}")
        has_entries = True

    if unique_fixes:
        lines.append("")
        lines.append("#### 🐛 Bug Fixes:")
        for item in unique_fixes:
            lines.append(f"- {item}")
        has_entries = True

    if unique_others:
        lines.append("")
        lines.append("#### 🔧 Other Improvements:")
        for item in unique_others:
            lines.append(f"- {item}")
        has_entries = True

    if not has_entries:
        lines.append("- *(No feature commit messages detected)*")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### 2. New API Endpoints:")

    unique_web = list(dict.fromkeys(api_web_lines or []))
    unique_mob = list(dict.fromkeys(api_mob_lines or []))

    if not unique_web and not unique_mob:
        lines.append("- *(No new API endpoints detected in commit messages)*")
    else:
        lines.append("")
        lines.append("**Web:**")
        if unique_web:
            for item in unique_web:
                lines.append(f"- {item}")
        else:
            lines.append("- *(None)*")

        lines.append("")
        lines.append("**Mobile:**")
        if unique_mob:
            for item in unique_mob:
                lines.append(f"- {item}")
        else:
            lines.append("- *(None)*")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### 3. Database Migrations:")
    if sql_files:
        sorted_sql = sorted(sql_files)
        lines.append(f"- `combined_db_scripts.sql` ({len(sorted_sql)} files compiled: {', '.join(Path(f).name for f in sorted_sql)})")
    else:
        lines.append("- *(No SQL migration scripts in this release)*")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### 4. Technical Audit (Commits by branch):")
    lines.append("")
    if branch_commit_blocks:
        lines.append("\n".join(branch_commit_blocks))

    return "\n".join(lines) + "\n"


def ensure_git_exclude(git_dir: Path, ignore_entry: str):
    """Item (7): Add output directory to .git/info/exclude to protect working tree."""
    try:
        info_dir = git_dir / "info"
        info_dir.mkdir(parents=True, exist_ok=True)
        exclude_file = info_dir / "exclude"
        existing = ""
        if exclude_file.exists():
            existing = exclude_file.read_text(encoding="utf-8")
        if ignore_entry not in existing:
            with open(exclude_file, "a", encoding="utf-8", newline="\n") as f:
                f.write(f"\n{ignore_entry}\n")
    except Exception:
        pass


def format_combined_sql(sql_files_data: dict[str, dict], version: str, branches: list[str], now_str: str) -> tuple[str, list[str]]:
    """
    Item (6) & (3): Formats combined SQL script with deterministic sorting,
    source checksums, and SQL safety scanning (DROP, TRUNCATE, DELETE without WHERE).
    Returns (sql_content, list_of_all_warnings).
    """
    warnings = []
    combined_body = []
    checksum_lines = []

    if sql_files_data:
        for sql_file in sorted(sql_files_data.keys()):
            data = sql_files_data[sql_file]
            file_branches = data["branches"]
            chosen_branch = file_branches[-1]
            chosen_hash = data["hashes"][chosen_branch]
            checksum_lines.append(f"--   * {sql_file} [sha256: {chosen_hash[:16]}...]")

            hashes = list(set(data["hashes"].values()))
            collision_warning = ""
            if len(hashes) > 1:
                collision_warning = (
                    f"-- [COLLISION WARNING] File '{sql_file}' was modified differently across branches: "
                    f"{', '.join(file_branches)}. Using version from '{file_branches[-1]}'."
                )
                warnings.append(f"SQL file '{sql_file}' has differing contents across branches: {', '.join(file_branches)}")

            content = data["contents"][chosen_branch]
            other_branches = ""
            if len(file_branches) > 1:
                other_branches = f" (Also present in: {', '.join(file_branches)})"

            combined_body.append("-- ----------------------------------------------------------------------")
            combined_body.append(f"-- FILE: {sql_file}")
            combined_body.append(f"-- SOURCE BRANCH: {chosen_branch}{other_branches}")
            if collision_warning:
                combined_body.append(collision_warning)
            combined_body.append("-- ----------------------------------------------------------------------")

            if content:
                combined_body.append(content.strip())
                combined_body.append("")

    full_body_str = "\n".join(combined_body)
    safety_warnings = scan_sql_safety(full_body_str)
    for sw in safety_warnings:
        warnings.append(sw)

    combined_sql_lines = []
    if safety_warnings:
        combined_sql_lines.extend([
            "-- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
            "-- [CRITICAL SECURITY WARNING / CẢNH BÁO AN TOÀN DỮ LIỆU]",
            "-- Potentially destructive SQL statements detected:"
        ])
        for sw in safety_warnings:
            combined_sql_lines.append(f"--   ! {sw}")
        combined_sql_lines.extend([
            "-- Review thoroughly before executing against staging or production DB!",
            "-- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
            ""
        ])

    combined_sql_lines.extend([
        "-- ======================================================================",
        f"-- COMBINED DATABASE RELEASE SCRIPT: {version}",
        f"-- Generated at: {now_str}",
        f"-- Source branches: {', '.join(branches)}"
    ])
    if checksum_lines:
        combined_sql_lines.append("-- Source files & SHA-256 Checksums:")
        combined_sql_lines.extend(checksum_lines)
    combined_sql_lines.extend([
        "-- ======================================================================",
        ""
    ])

    if not sql_files_data:
        combined_sql_lines.append("-- [INFO] No SQL migration scripts detected across these branches.\n")
    else:
        combined_sql_lines.append(full_body_str)

    return "\n".join(combined_sql_lines) + "\n", warnings


def main():
    # Parse CLI Arguments using argparse (Item 3)
    parser = argparse.ArgumentParser(
        description="Consolidate marked Git branches into a local release bundle."
    )
    parser.add_argument(
        "version",
        nargs="?",
        default="",
        help="Release version name (e.g. uat-1.1.3). Only [A-Za-z0-9._-] allowed."
    )
    parser.add_argument(
        "--fresh",
        "-fresh",
        "--clean",
        "-clean",
        dest="fresh",
        action="store_true",
        help="Overwrite target version bundle from scratch without merging previous branches."
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Simulate release bundle compilation without writing files or clearing marked branches."
    )
    parser.add_argument(
        "--base",
        "-b",
        dest="base",
        default="",
        help="Custom base branch to diff against (e.g. develop, main, staging)."
    )
    parser.add_argument(
        "extra_args",
        nargs="*",
        help="Optional positional base branch or extra arguments."
    )

    parsed_args = parser.parse_args()

    # Allow passing base branch positionally as 2nd argument (e.g. bundle-local v1.0.0 develop)
    if not parsed_args.base and parsed_args.extra_args:
        parsed_args.base = parsed_args.extra_args[0]

    # 1. Verify Git repository (Item 8)
    code, git_root_str = run_git(["rev-parse", "--show-toplevel"])
    if code != 0 or not git_root_str:
        print("[ERROR] Current directory is not a Git repository.", file=sys.stderr)
        sys.exit(1)

    git_root = Path(git_root_str)
    code, git_dir_str = run_git(["rev-parse", "--git-dir"])
    git_dir = (git_root / git_dir_str).resolve() if (code == 0 and git_dir_str) else (git_root / ".git").resolve()

    # Check for empty repository (Item 8)
    code, _ = run_git(["rev-parse", "HEAD"])
    if code != 0:
        print("[ERROR] Git repository has no commits (empty repository). Create an initial commit first.", file=sys.stderr)
        sys.exit(2)

    # 2. Check marked branches file (Item 8)
    marked_file = git_dir / "marked_branches.txt"
    if not marked_file.exists():
        print("[WARN] No branches currently marked. Mark branches first with 'git mark <branch>'.", file=sys.stderr)
        sys.exit(2)

    raw_branches = [
        line.strip()
        for line in marked_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    branches = list(dict.fromkeys(raw_branches))
    if not branches:
        print("[WARN] Marked branches list is empty.", file=sys.stderr)
        sys.exit(2)

    # 3. Validate Version Name (Item 1)
    version = parsed_args.version.strip()
    if not version:
        version = f"release-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        if not validate_version_name(version):
            print(
                f"[ERROR] Invalid version name '{version}'.\n"
                "Version name must only contain alphanumeric characters, dots, underscores, or dashes [A-Za-z0-9._-],\n"
                "must start with an alphanumeric character, and cannot contain path traversal ('..').",
                file=sys.stderr
            )
            sys.exit(1)

    # Check for uncommitted SQL files in working tree (excluding release_output and .antigravity)
    code, status_out = run_git(["status", "--porcelain", "*.sql"])
    if code == 0 and status_out:
        uncommitted_sql = [
            line for line in status_out.splitlines()
            if "release_output" not in line and ".antigravity" not in line
        ]
        if uncommitted_sql:
            print("\n" + "=" * 60)
            print("[WARNING] Uncommitted SQL files detected in working tree:")
            for item in uncommitted_sql:
                print(f"   {item}")
            print("Note: Only COMMITTED SQL files will be extracted into the release bundle.")
            print("=" * 60 + "\n")

    # 4. Determine Base Branch (Item 5)
    custom_base = parsed_args.base.strip()
    base_branch = "develop"
    if custom_base:
        code, _ = run_git(["rev-parse", "--verify", "--quiet", custom_base])
        if code == 0:
            base_branch = custom_base
        else:
            print(f"[WARN] Base branch '{custom_base}' not found, falling back to auto-detection...")

    if not custom_base or base_branch != custom_base:
        candidate_bases = ["develop", "dev", "main", "master"]
        found = False
        for cand in candidate_bases:
            code, _ = run_git(["rev-parse", "--verify", "--quiet", cand])
            if code == 0:
                base_branch = cand
                found = True
                break
        if not found:
            _, cur = run_git(["branch", "--show-current"])
            base_branch = cur if cur else "main"

    is_dry_run = parsed_args.dry_run

    # 5. Determine Output Directory (.antigravity precedence) and Defense-in-depth resolve check
    antigravity_dir = git_root / ".antigravity"
    if antigravity_dir.exists() and antigravity_dir.is_dir():
        base_output_dir = (antigravity_dir / "release_output").resolve()
        ignore_entry = ".antigravity/release_output/"
    else:
        base_output_dir = (git_root / "release_output").resolve()
        ignore_entry = "release_output/"

    target_dir = (base_output_dir / version).resolve()

    # Defense-in-depth: Ensure target_dir is strictly inside base_output_dir (Item 1)
    if not str(target_dir).startswith(str(base_output_dir)):
        print(f"[SECURITY ERROR] Path traversal detected for version: '{version}'", file=sys.stderr)
        sys.exit(1)

    if not is_dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        # Item (7): Automatically add to .git/info/exclude without dirtying .gitignore
        ensure_git_exclude(git_dir, ignore_entry)

    # 6. Branch validation, SHAs, and Smart Accumulate (unless --fresh)
    is_fresh_mode = parsed_args.fresh
    branches_file = target_dir / "branches.txt"
    branch_shas: dict[str, str] = {}
    valid_branches: list[str] = []

    # Check for deleted or already merged branches
    for b in branches:
        code, _ = run_git(["rev-parse", "--verify", "--quiet", b])
        if code != 0:
            print(f"[WARN] Branch '{b}' no longer exists locally. Skipping.")
            continue

        # Check if already merged into base
        code, _ = run_git(["merge-base", "--is-ancestor", b, base_branch])
        if code == 0:
            print(f"[NOTICE] Branch '{b}' is already fully merged into '{base_branch}'.")

        _, sha = run_git(["rev-parse", "--short", b])
        branch_shas[b] = sha if sha else "unknown"
        valid_branches.append(b)

    if not valid_branches:
        print("[ERROR] None of the marked branches could be resolved locally.", file=sys.stderr)
        sys.exit(2)

    active_branches = valid_branches
    if branches_file.exists() and not is_fresh_mode and not is_dry_run:
        old_branches = []
        for line in branches_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split()
                if parts:
                    old_branches.append(parts[0])
        merged = list(dict.fromkeys(old_branches + active_branches))
        new_count = len(merged) - len(old_branches)
        print(f"\n[UPDATE] Release version '{version}' already exists!")
        print(f"-> Merged {len(old_branches)} existing branches + {new_count} newly marked branches.")
        print(f"-> Total branches in release: {len(merged)}.\n")
        active_branches = merged
    elif is_fresh_mode and target_dir.exists() and not is_dry_run:
        print(f"\n[FRESH] Fresh mode enabled: Overwriting '{version}' with {len(active_branches)} new branches.\n")

    # Item (1): Format branches.txt with commit SHA and timestamp
    branches_file_lines = [
        f"# Release: {version}",
        f"# Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Base branch: {base_branch}",
    ]
    for b in active_branches:
        sha = branch_shas.get(b, "")
        if not sha:
            _, sha = run_git(["rev-parse", "--short", b])
            sha = sha if sha else "unknown"
            branch_shas[b] = sha
        branches_file_lines.append(f"{b} {sha}")

    if not is_dry_run:
        branches_file.write_text("\n".join(branches_file_lines) + "\n", encoding="utf-8")

    # 7. Collect Commits (Changelog) & SQL files
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    features = []
    fixes = []
    others = []
    api_web_lines = []
    api_mob_lines = []
    branch_commit_blocks = []

    # Map: sql_file_path -> dict(hashes={branch: sha256}, contents={branch: str}, branches=[])
    sql_files_data: dict[str, dict] = {}

    for b in active_branches:
        code, _ = run_git(["rev-parse", "--verify", "--quiet", b])
        if code != 0:
            continue

        _, merge_base = run_git(["merge-base", base_branch, b])
        if not merge_base:
            merge_base = base_branch

        # Collect commit messages
        code, commits_raw = run_git(["log", f"{merge_base}..{b}", "--no-merges", "--format=%s"])
        if code == 0 and commits_raw:
            for cmsg in commits_raw.splitlines():
                # Extract API endpoint if formatted
                api_info = extract_api_endpoint(cmsg)
                if api_info:
                    plat, api_entry = api_info
                    if plat == "web":
                        api_web_lines.append(api_entry)
                    else:
                        api_mob_lines.append(api_entry)

                cat, clean_msg = categorize_commit(cmsg)
                if clean_msg:
                    if cat == "features":
                        features.append(clean_msg)
                    elif cat == "fixes":
                        fixes.append(clean_msg)
                    else:
                        others.append(clean_msg)

        # Technical audit entries
        branch_block = [f"#### Branch: `{b}`"]
        code, raw_commits = run_git(["log", f"{merge_base}..{b}", "--no-merges", "--format=- [%h] %s *(%an, %cr)*"])
        if code == 0 and raw_commits:
            branch_block.append(raw_commits)
        else:
            branch_block.append("- *(No unique commits compared to base)*")
        branch_block.append("")
        branch_commit_blocks.append("\n".join(branch_block))

        # SQL diff (filter out deleted files)
        code, sql_files_raw = run_git(["diff", "--name-only", "--diff-filter=ACMR", f"{merge_base}..{b}", "--", "*.sql"])
        if code == 0 and sql_files_raw:
            for sql_f in sql_files_raw.splitlines():
                sql_f = sql_f.strip().replace("\\", "/")
                if not sql_f:
                    continue
                if sql_f not in sql_files_data:
                    sql_files_data[sql_f] = {"branches": [], "hashes": {}, "contents": {}}

                content = read_git_file(b, sql_f)
                content_hash = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
                sql_files_data[sql_f]["branches"].append(b)
                sql_files_data[sql_f]["hashes"][b] = content_hash
                sql_files_data[sql_f]["contents"][b] = content

    # Build Changelog
    changelog_path = target_dir / "CHANGELOG_LOCAL.md"
    changelog_content = format_changelog(
        version=version,
        base_branch=base_branch,
        branches=active_branches,
        now_str=now_str,
        features=features,
        fixes=fixes,
        others=others,
        api_web_lines=api_web_lines,
        api_mob_lines=api_mob_lines,
        sql_files=list(sql_files_data.keys()),
        branch_commit_blocks=branch_commit_blocks
    )

    # 8. Combine SQL files with deterministic sorting & safety check
    combined_sql_path = target_dir / "combined_db_scripts.sql"
    combined_sql_text, warnings = format_combined_sql(sql_files_data, version, active_branches, now_str)
    for w in warnings:
        print(f"[SECURITY/WARNING] {w}")

    # Build release_meta.json
    meta_path = target_dir / "release_meta.json"
    meta_data = {
        "version": version,
        "created_at": now_str,
        "base_branch": base_branch,
        "branches": [{"name": b, "commit_sha": branch_shas.get(b, "")} for b in active_branches],
        "highlights_count": {
            "features": len(list(dict.fromkeys(features))),
            "fixes": len(list(dict.fromkeys(fixes))),
            "others": len(list(dict.fromkeys(others)))
        },
        "api_endpoints": {
            "web": list(dict.fromkeys(api_web_lines)),
            "mobile": list(dict.fromkeys(api_mob_lines))
        },
        "sql_files": [
            {
                "file": f,
                "sha256": sql_files_data[f]["hashes"].get(sql_files_data[f]["branches"][-1], "")
            }
            for f in sorted(sql_files_data.keys())
        ],
        "warnings": warnings
    }

    if is_dry_run:
        print("\n" + "=" * 60)
        print(f" [DRY-RUN COMPLETE] Release '{version}' simulated successfully!")
        print(f" Target Directory would be: {target_dir}")
        print(f" - Branches to bundle:       {len(active_branches)}")
        print(f" - Features / Fixes / Others: {len(features)} / {len(fixes)} / {len(others)}")
        print(f" - SQL migration files:      {len(sql_files_data)}")
        print(f" - Total warnings:           {len(warnings)}")
        print(" (No files written to disk, marked_branches.txt preserved)")
        print("=" * 60 + "\n")
        sys.exit(0)

    # Write files to disk (Item 2: Explicit UTF-8)
    with open(changelog_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(changelog_content)

    with open(combined_sql_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(combined_sql_text)

    with open(meta_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta_data, f, indent=2, ensure_ascii=False)

    # 9. Clean up marked_branches.txt
    marked_file.unlink(missing_ok=True)

    print("=" * 60)
    print(f" [SUCCESS] LOCAL RELEASE BUNDLE COMPILED: {version}")
    print(f" Target Directory: {target_dir}")
    print(f"   1. Changelog:     {changelog_path}")
    print(f"   2. Combined SQL:  {combined_sql_path}")
    print(f"   3. Metadata JSON: {meta_path}")
    print(f"   4. Source List:   {branches_file}")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
