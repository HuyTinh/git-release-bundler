---
name: git-mark
description: Mark the current or specified Git branch for local release bundling (.git/marked_branches.txt). Triggered when the user invokes /git-mark, /mark, /git-mark list, /mark list, /git-mark clear, /mark clear, /git-mark unmark <branch>, or says "mark nhánh này", "đánh dấu nhánh", "bỏ đánh dấu nhánh".
---

# Git Mark Branch Skill

Mark Git branches for local release preparation and consolidation into a release bundle (`/bundle-local`).

## Supported Commands & Syntaxes
- `/git-mark` or `/mark`: Mark the currently checked-out branch.
- `/git-mark <branch_name>` or `/mark <branch_name>`: Mark an explicit branch (even if not currently checked out).
- `/git-mark list` or `/mark list`: Display all currently marked branches awaiting release.
- `/git-mark unmark <branch_name>` or `/mark rm <branch_name>`: Remove an individual branch from the pending list.
- `/git-mark clear` or `/mark clear`: Clear the entire marked list.

## Execution Directives
When invoked:
1. Run using the global Git alias:
   ```bash
   git mark [action_or_branch_name] [target_branch_if_any]
   ```
   *(Or direct script execution: `python "<path>/mark.py" [args]`)*
2. Respond with a concise, formatted summary in the user's conversational language.
