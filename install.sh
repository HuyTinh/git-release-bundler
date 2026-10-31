#!/usr/bin/env bash
# ==============================================================================
# git-release-bundler: 1-Click Installer (macOS / Linux)
# ==============================================================================
set -e

# 1. Detect and verify Python >= 3.8 (Item 4)
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "[ERROR] Python 3 is not installed or not in PATH."
        exit 1
    fi
fi

if ! "$PYTHON_CMD" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "[ERROR] Python >= 3.8 is required. Current: $("$PYTHON_CMD" --version)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/skills"

if [ ! -d "$SKILLS_SRC" ]; then
    echo "[ERROR] 'skills' directory not found in: $SCRIPT_DIR"
    exit 1
fi

GEMINI_SKILLS_DIR="$HOME/.gemini/config/skills"

echo "=========================================================="
echo " Installing git-release-bundler (Python Engine)..."
echo " Detected Python: $PYTHON_CMD (>= 3.8)"
echo "=========================================================="

# 2. Deploy to Gemini / Antigravity skills
mkdir -p "$GEMINI_SKILLS_DIR/git-mark" "$GEMINI_SKILLS_DIR/bundle-local"
cp -R "$SKILLS_SRC/git-mark/"* "$GEMINI_SKILLS_DIR/git-mark/"
cp -R "$SKILLS_SRC/bundle-local/"* "$GEMINI_SKILLS_DIR/bundle-local/"
echo " [OK] Installed skills to Antigravity: $GEMINI_SKILLS_DIR"

# 3. Deploy to Claude Code skills (~/.claude/skills) if applicable (Item 9)
CLAUDE_DIR="$HOME/.claude"
if [ -d "$CLAUDE_DIR" ]; then
    CLAUDE_SKILLS_DIR="$CLAUDE_DIR/skills"
    mkdir -p "$CLAUDE_SKILLS_DIR/git-mark" "$CLAUDE_SKILLS_DIR/bundle-local"
    cp -R "$SKILLS_SRC/git-mark/"* "$CLAUDE_SKILLS_DIR/git-mark/"
    cp -R "$SKILLS_SRC/bundle-local/"* "$CLAUDE_SKILLS_DIR/bundle-local/"
    echo " [OK] Installed skills to Claude Code: $CLAUDE_SKILLS_DIR"
fi

MARK_SCRIPT="$GEMINI_SKILLS_DIR/git-mark/scripts/mark.py"
BUNDLE_SCRIPT="$GEMINI_SKILLS_DIR/bundle-local/scripts/bundle_local.py"

chmod +x "$MARK_SCRIPT" "$BUNDLE_SCRIPT"

# 4. Configure Git Aliases globally (Items 3, 4)
EXISTING_MARK="$(git config --global --get alias.mark 2>/dev/null || true)"
EXISTING_BUNDLE="$(git config --global --get alias.bundle-local 2>/dev/null || true)"

if [ -n "$EXISTING_MARK" ]; then
    echo "[WARN] Existing 'git mark' alias detected: $EXISTING_MARK (Overwriting)"
fi
if [ -n "$EXISTING_BUNDLE" ]; then
    echo "[WARN] Existing 'git bundle-local' alias detected: $EXISTING_BUNDLE (Overwriting)"
fi

# Remove redundant alias git-git-mark (Item 4)
git config --global --unset-all alias.git-mark 2>/dev/null || true

# Item (3): Use "$@" in alias
git config --global alias.mark "!f() { $PYTHON_CMD \"$MARK_SCRIPT\" \"\$@\"; }; f"
git config --global alias.bundle-local "!f() { $PYTHON_CMD \"$BUNDLE_SCRIPT\" \"\$@\"; }; f"

echo " [OK] Configured Git global aliases:"
echo "      - git mark"
echo "      - git bundle-local"

echo ""
echo "=========================================================="
echo " SUCCESS! git-release-bundler installed successfully!"
echo "=========================================================="
