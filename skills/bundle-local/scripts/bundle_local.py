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
        r'(?:feat|fix|chore|docs|refactor|update|style|perf|test|build|ci|revert)'
        r'(?:\([^\)]+\))?!?:'
        r'\s*'
    )

    clean = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
    if clean:
        clean = clean[0].upper() + clean[1:]
    return clean if clean else text


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
    Item (6): Formats combined SQL script with deterministic sorting and collision detection.
    Returns (sql_content, list_of_collision_warnings).
    """
    combined_sql_lines = [
        "-- ======================================================================",
        f"-- COMBINED DATABASE RELEASE SCRIPT: {version}",
        f"-- Generated at: {now_str}",
        f"-- Source branches: {', '.join(branches)}",
        "-- ======================================================================",
        ""
    ]
    warnings = []

    if not sql_files_data:
        combined_sql_lines.append("-- [INFO] No SQL migration scripts detected across these branches.\n")
    else:
        # Deterministic sorting by path name
        for sql_file in sorted(sql_files_data.keys()):
            data = sql_files_data[sql_file]
            file_branches = data["branches"]
            hashes = list(set(data["hashes"].values()))

            collision_warning = ""
            if len(hashes) > 1:
                collision_warning = (
                    f"-- [COLLISION WARNING] File '{sql_file}' was modified differently across branches: "
                    f"{', '.join(file_branches)}. Using version from '{file_branches[-1]}'."
                )
                warnings.append(f"SQL file '{sql_file}' has differing contents across branches: {', '.join(file_branches)}")

            chosen_branch = file_branches[-1]
            content = data["contents"][chosen_branch]

            other_branches = ""
            if len(file_branches) > 1:
                other_branches = f" (Also present in: {', '.join(file_branches)})"

            combined_sql_lines.append("-- ----------------------------------------------------------------------")
            combined_sql_lines.append(f"-- FILE: {sql_file}")
            combined_sql_lines.append(f"-- SOURCE BRANCH: {chosen_branch}{other_branches}")
            if collision_warning:
                combined_sql_lines.append(collision_warning)
            combined_sql_lines.append("-- ----------------------------------------------------------------------")

            if content:
                combined_sql_lines.append(content.strip())
                combined_sql_lines.append("")

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
        "--base",
        "-b",
        dest="base",
        default="",
        help="Custom base branch to diff against (e.g. develop, main, staging)."
    )

    parsed_args = parser.parse_args()

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

    target_dir.mkdir(parents=True, exist_ok=True)

    # Item (7): Automatically add to .git/info/exclude without dirtying .gitignore
    ensure_git_exclude(git_dir, ignore_entry)

    # 6. Save branches.txt (Smart Accumulate unless --fresh)
    is_fresh_mode = parsed_args.fresh
    branches_file = target_dir / "branches.txt"
    if branches_file.exists() and not is_fresh_mode:
        old_branches = [
            line.strip()
            for line in branches_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        merged = list(dict.fromkeys(old_branches + branches))
        new_count = len(merged) - len(old_branches)
        print(f"\n[UPDATE] Release version '{version}' already exists!")
        print(f"-> Merged {len(old_branches)} existing branches + {new_count} newly marked branches.")
        print(f"-> Total branches in release: {len(merged)}.\n")
        branches = merged
    elif is_fresh_mode and target_dir.exists():
        print(f"\n[FRESH] Fresh mode enabled: Overwriting '{version}' with {len(branches)} new branches.\n")

    branches_file.write_text("\n".join(branches) + "\n", encoding="utf-8")

    # 7. Collect Commits (Changelog) & SQL files
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    changelog_lines = [
        f"# Release Changelog: {version}",
        f"- **Created at:** {now_str}",
        f"- **Base branch:** `{base_branch}`",
        f"- **Branch count:** {len(branches)}",
        "",
        "### Features & Business Highlights (Ready-to-copy):"
    ]

    business_lines = []
    branch_commit_blocks = []

    # Map: sql_file_path -> dict(hashes={branch: sha256}, contents={branch: str}, branches=[])
    sql_files_data: dict[str, dict] = {}

    for b in branches:
        code, _ = run_git(["rev-parse", "--verify", "--quiet", b])
        if code != 0:
            print(f"[WARN] Branch '{b}' could not be resolved locally. Skipping.")
            continue

        _, merge_base = run_git(["merge-base", base_branch, b])
        if not merge_base:
            merge_base = base_branch

        # Collect commit messages
        code, commits_raw = run_git(["log", f"{merge_base}..{b}", "--no-merges", "--format=%s"])
        if code == 0 and commits_raw:
            for cmsg in commits_raw.splitlines():
                clean_msg = clean_commit_message(cmsg)
                if clean_msg:
                    business_lines.append(f"- {clean_msg}")

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

    # Deduplicate business summary
    unique_business = list(dict.fromkeys(business_lines))
    if unique_business:
        changelog_lines.extend(unique_business)
    else:
        changelog_lines.append("- *(No feature commit messages detected)*")

    changelog_lines.append("")
    changelog_lines.append("---")
    changelog_lines.append("### Technical Audit (Commits by branch):")
    changelog_lines.append("")
    changelog_lines.append("\n".join(branch_commit_blocks))

    # Write Changelog (Item 2: Explicit UTF-8)
    changelog_path = target_dir / "CHANGELOG_LOCAL.md"
    with open(changelog_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(changelog_lines) + "\n")

    # 8. Combine SQL files with deterministic sorting & collision detection (Item 6)
    combined_sql_path = target_dir / "combined_db_scripts.sql"
    combined_sql_text, warnings = format_combined_sql(sql_files_data, version, branches, now_str)
    for w in warnings:
        print(f"[COLLISION WARNING] {w}")

    with open(combined_sql_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(combined_sql_text)

    # 9. Clean up marked_branches.txt
    marked_file.unlink(missing_ok=True)

    print("=" * 60)
    print(f" [SUCCESS] LOCAL RELEASE BUNDLE COMPILED: {version}")
    print(f" Target Directory: {target_dir}")
    print(f"   1. Changelog:     {changelog_path}")
    print(f"   2. Combined SQL:  {combined_sql_path}")
    print(f"   3. Source List:   {branches_file}")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
