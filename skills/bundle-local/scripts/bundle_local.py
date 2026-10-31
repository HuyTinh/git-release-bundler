#!/usr/bin/env python3
"""
git-bundle-local: Consolidate marked Git branches into a versioned local release bundle.
Generates 2-tier CHANGELOG_LOCAL.md and combined_db_scripts.sql.
Zero dependencies (Standard Library only). Cross-platform (Windows, macOS, Linux).
"""

import sys
import re
import datetime
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


def main():
    # 1. Verify Git repository
    code, git_root_str = run_git(["rev-parse", "--show-toplevel"])
    if code != 0 or not git_root_str:
        print("[ERROR] Current directory is not a Git repository.", file=sys.stderr)
        sys.exit(1)

    git_root = Path(git_root_str)
    code, git_dir_str = run_git(["rev-parse", "--git-dir"])
    git_dir = git_root / (git_dir_str if code == 0 and git_dir_str else ".git")

    # 2. Check marked branches file
    marked_file = git_dir / "marked_branches.txt"
    if not marked_file.exists():
        print("[WARN] No branches currently marked. Use 'git mark' first.")
        sys.exit(0)

    raw_branches = [
        line.strip()
        for line in marked_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    # Deduplicate while preserving order
    branches = list(dict.fromkeys(raw_branches))
    if not branches:
        print("[WARN] Marked branches list is empty.")
        sys.exit(0)

    # Parse CLI Arguments
    args = sys.argv[1:]
    version_arg = args[0].strip() if len(args) > 0 else ""
    mode_or_base = args[1].strip() if len(args) > 1 else ""

    is_fresh_mode = mode_or_base.lower() in ["-fresh", "--fresh", "-clean", "--clean"]
    custom_base = mode_or_base if (mode_or_base and not is_fresh_mode) else ""

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

    # 3. Determine Base Branch (customBase -> develop -> dev -> main -> master)
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

    # 4. Sanitize Version Name
    if not version_arg:
        version_arg = f"release-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        # Sanitize Windows illegal characters: \ / : * ? " < > |
        version_arg = re.sub(r'[\\/:*?"<>|]', '-', version_arg.strip())

    # 5. Determine Output Directory (.antigravity precedence)
    antigravity_dir = git_root / ".antigravity"
    if antigravity_dir.exists() and antigravity_dir.is_dir():
        base_output_dir = antigravity_dir / "release_output"
    else:
        base_output_dir = git_root / "release_output"

    target_dir = base_output_dir / version_arg
    target_dir.mkdir(parents=True, exist_ok=True)

    # Ensure output dir is added to .gitignore
    gitignore_file = git_root / ".gitignore"
    ignore_entry = ".antigravity/release_output/" if (antigravity_dir.exists()) else "release_output/"
    if gitignore_file.exists():
        gi_content = gitignore_file.read_text(encoding="utf-8")
        if ignore_entry not in gi_content:
            with open(gitignore_file, "a", encoding="utf-8") as f:
                f.write(f"\n{ignore_entry}\n")

    # 6. Save branches.txt (Smart Accumulate)
    branches_file = target_dir / "branches.txt"
    if branches_file.exists() and not is_fresh_mode:
        old_branches = [
            line.strip()
            for line in branches_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        merged = list(dict.fromkeys(old_branches + branches))
        new_count = len(merged) - len(old_branches)
        print(f"\n[UPDATE] Release version '{version_arg}' already exists!")
        print(f"-> Merged {len(old_branches)} existing branches + {new_count} newly marked branches.")
        print(f"-> Total branches in release: {len(merged)}.\n")
        branches = merged
    elif is_fresh_mode and target_dir.exists():
        print(f"\n[FRESH] Fresh mode enabled: Overwriting '{version_arg}' with {len(branches)} new branches.\n")

    branches_file.write_text("\n".join(branches) + "\n", encoding="utf-8")

    # 7. Collect Commits (Changelog) & SQL files
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    changelog_lines = [
        f"# Release Changelog: {version_arg}",
        f"- **Created at:** {now_str}",
        f"- **Base branch:** `{base_branch}`",
        f"- **Branch count:** {len(branches)}",
        "",
        "### Features & Business Highlights (Ready-to-copy):"
    ]

    business_lines = []
    branch_commit_blocks = []
    sql_files_map: dict[str, list[str]] = {}

    commit_clean_regex = re.compile(
        r'^(\[[^\]]+\]\s*|[A-Z]+-\d+[:\s]+)?(feat|fix|chore|docs|refactor|update|style|perf|test|build|ci)(\([^\)]+\))?:\s*',
        re.IGNORECASE
    )

    for b in branches:
        code, _ = run_git(["rev-parse", "--verify", "--quiet", b])
        if code != 0:
            continue

        _, merge_base = run_git(["merge-base", base_branch, b])
        if not merge_base:
            merge_base = base_branch

        # Business summary entries
        code, commits_raw = run_git(["log", f"{merge_base}..{b}", "--no-merges", "--format=%s"])
        if code == 0 and commits_raw:
            for cmsg in commits_raw.splitlines():
                cmsg = cmsg.strip()
                if not cmsg:
                    continue
                clean_msg = commit_clean_regex.sub("", cmsg).strip()
                if clean_msg:
                    clean_msg = clean_msg[0].upper() + clean_msg[1:]
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

        # SQL diff
        code, sql_files_raw = run_git(["diff", "--name-only", "--diff-filter=ACMR", f"{merge_base}..{b}", "--", "*.sql"])
        if code == 0 and sql_files_raw:
            for sql_f in sql_files_raw.splitlines():
                sql_f = sql_f.strip().replace("\\", "/")
                if not sql_f:
                    continue
                if sql_f not in sql_files_map:
                    sql_files_map[sql_f] = []
                if b not in sql_files_map[sql_f]:
                    sql_files_map[sql_f].append(b)

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

    # Write Changelog
    changelog_path = target_dir / "CHANGELOG_LOCAL.md"
    changelog_path.write_text("\n".join(changelog_lines) + "\n", encoding="utf-8")

    # 8. Combine SQL files (Safe reading via git show without checkout)
    combined_sql_path = target_dir / "combined_db_scripts.sql"
    combined_sql_lines = [
        "-- ======================================================================",
        f"-- COMBINED DATABASE RELEASE SCRIPT: {version_arg}",
        f"-- Generated at: {now_str}",
        f"-- Source branches: {', '.join(branches)}",
        "-- ======================================================================",
        ""
    ]

    if not sql_files_map:
        combined_sql_lines.append("-- [INFO] No SQL migration scripts detected across these branches.\n")
    else:
        for sql_file in sorted(sql_files_map.keys()):
            source_branch = sql_files_map[sql_file][0]
            other_branches = ""
            if len(sql_files_map[sql_file]) > 1:
                other_branches = f" (Also present in: {', '.join(sql_files_map[sql_file])})"

            combined_sql_lines.append("-- ----------------------------------------------------------------------")
            combined_sql_lines.append(f"-- FILE: {sql_file}")
            combined_sql_lines.append(f"-- SOURCE BRANCH: {source_branch}{other_branches}")
            combined_sql_lines.append("-- ----------------------------------------------------------------------")

            file_content = read_git_file(source_branch, sql_file)
            if file_content:
                combined_sql_lines.append(file_content.strip())
                combined_sql_lines.append("")

    combined_sql_path.write_text("\n".join(combined_sql_lines) + "\n", encoding="utf-8")

    # 9. Clean up marked_branches.txt
    marked_file.unlink(missing_ok=True)

    print("=" * 60)
    print(f" [SUCCESS] LOCAL RELEASE BUNDLE COMPILED: {version_arg}")
    print(f" Target Directory: {target_dir}")
    print(f"   1. Changelog:     {changelog_path}")
    print(f"   2. Combined SQL:  {combined_sql_path}")
    print(f"   3. Source List:   {branches_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
