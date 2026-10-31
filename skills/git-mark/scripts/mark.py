#!/usr/bin/env python3
"""
git-mark: Mark Git branches for local release bundling.
Zero dependencies (Standard Library only). Cross-platform (Windows, macOS, Linux).
"""

import sys
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


def main():
    # 1. Verify Git repository
    code, git_root = run_git(["rev-parse", "--show-toplevel"])
    if code != 0 or not git_root:
        print("[ERROR] Current directory is not a Git repository.", file=sys.stderr)
        sys.exit(1)

    code, git_dir = run_git(["rev-parse", "--git-dir"])
    if code != 0 or not git_dir:
        git_dir = ".git"

    marked_file = Path(git_root) / git_dir / "marked_branches.txt"

    args = sys.argv[1:]
    action_or_branch = args[0].strip() if len(args) > 0 else ""
    target_branch = args[1].strip() if len(args) > 1 else ""

    # 2. Action: list
    if action_or_branch in ["list", "-l", "--list"]:
        if marked_file.exists():
            lines = [
                line.strip()
                for line in marked_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if lines:
                print(f"\nMarked branches awaiting release ({len(lines)} branches):")
                for i, b in enumerate(lines, 1):
                    print(f"  {i:2}. {b}")
                print()
            else:
                print("No branches currently marked.")
        else:
            print("No branches currently marked.")
        sys.exit(0)

    # 3. Action: clear
    if action_or_branch in ["clear", "-c", "--clear"]:
        if marked_file.exists():
            marked_file.unlink(missing_ok=True)
        print("[OK] Cleared all marked branches.")
        sys.exit(0)

    # 4. Action: unmark / rm
    if action_or_branch in ["unmark", "rm", "remove", "-d", "--delete"]:
        branch_to_remove = target_branch
        if not branch_to_remove:
            _, branch_to_remove = run_git(["branch", "--show-current"])

        branch_to_remove = branch_to_remove.strip()
        if marked_file.exists():
            lines = [
                line.strip()
                for line in marked_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if branch_to_remove in lines:
                updated = [b for b in lines if b != branch_to_remove]
                if updated:
                    marked_file.write_text("\n".join(updated) + "\n", encoding="utf-8")
                else:
                    marked_file.unlink(missing_ok=True)
                print(f"[OK] Unmarked branch '{branch_to_remove}' ({len(updated)} branches remaining).")
            else:
                print(f"[WARN] Branch '{branch_to_remove}' was not found in the marked list.")
        else:
            print("[WARN] No branches currently marked.")
        sys.exit(0)

    # 5. Action: default mark
    branch_to_mark = action_or_branch
    if not branch_to_mark:
        _, branch_to_mark = run_git(["branch", "--show-current"])

    branch_to_mark = branch_to_mark.strip()
    if not branch_to_mark:
        print("[ERROR] Could not determine current branch. Please specify branch name (e.g. git mark feat/order).", file=sys.stderr)
        sys.exit(1)

    # Typo check: warn if marking an explicit branch that doesn't exist locally or on origin
    _, current_branch = run_git(["branch", "--show-current"])
    if branch_to_mark != current_branch:
        code_local, _ = run_git(["rev-parse", "--verify", "--quiet", branch_to_mark])
        if code_local != 0:
            code_remote, _ = run_git(["rev-parse", "--verify", "--quiet", f"origin/{branch_to_mark}"])
            if code_remote != 0:
                print(f"[WARNING] Branch '{branch_to_mark}' does not exist in local or remote Git. Please verify spelling.")

    existing = []
    if marked_file.exists():
        existing = [
            line.strip()
            for line in marked_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    if branch_to_mark in existing:
        print(f"[INFO] Branch '{branch_to_mark}' is already marked ({len(existing)} branches waiting).")
    else:
        existing.append(branch_to_mark)
        marked_file.write_text("\n".join(existing) + "\n", encoding="utf-8")
        print(f"[OK] Marked branch: {branch_to_mark} (Total: {len(existing)} branches waiting).")


if __name__ == "__main__":
    main()
