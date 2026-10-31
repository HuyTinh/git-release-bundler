#!/usr/bin/env bash
# ==============================================================================
# git-release-bundler: 1-Click Uninstaller (macOS / Linux)
# ==============================================================================
set -e

GEMINI_SKILLS_DIR="$HOME/.gemini/config/skills"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"

echo "Uninstalling git-release-bundler..."

rm -rf "$GEMINI_SKILLS_DIR/git-mark"
rm -rf "$GEMINI_SKILLS_DIR/bundle-local"

if [ -d "$CLAUDE_SKILLS_DIR" ]; then
    rm -rf "$CLAUDE_SKILLS_DIR/git-mark"
    rm -rf "$CLAUDE_SKILLS_DIR/bundle-local"
fi

git config --global --unset-all alias.mark 2>/dev/null || true
git config --global --unset-all alias.bundle-local 2>/dev/null || true
git config --global --unset-all alias.git-mark 2>/dev/null || true

echo "[SUCCESS] Uninstalled successfully!"
