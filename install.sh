#!/usr/bin/env bash
# ==============================================================================
# git-release-bundler: 1-Click Installer (macOS / Linux)
# ==============================================================================
set -e

# Detect Python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "[ERROR] Python 3 is not installed or not in PATH."
        exit 1
    fi
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
echo " Detected Python: $PYTHON_CMD"
echo "=========================================================="

mkdir -p "$GEMINI_SKILLS_DIR/git-mark" "$GEMINI_SKILLS_DIR/bundle-local"

cp -R "$SKILLS_SRC/git-mark/"* "$GEMINI_SKILLS_DIR/git-mark/"
cp -R "$SKILLS_SRC/bundle-local/"* "$GEMINI_SKILLS_DIR/bundle-local/"

echo " [OK] Installed skills to: $GEMINI_SKILLS_DIR"

MARK_SCRIPT="$GEMINI_SKILLS_DIR/git-mark/scripts/mark.py"
BUNDLE_SCRIPT="$GEMINI_SKILLS_DIR/bundle-local/scripts/bundle_local.py"

chmod +x "$MARK_SCRIPT" "$BUNDLE_SCRIPT"

git config --global alias.mark "!$PYTHON_CMD \"$MARK_SCRIPT\""
git config --global alias.git-mark "!$PYTHON_CMD \"$MARK_SCRIPT\""
git config --global alias.bundle-local "!f() { $PYTHON_CMD \"$BUNDLE_SCRIPT\" \"\$1\" \"\$2\"; }; f"

echo " [OK] Configured Git global aliases:"
echo "      - git mark"
echo "      - git git-mark"
echo "      - git bundle-local"

echo ""
echo "=========================================================="
echo " SUCCESS! git-release-bundler installed successfully!"
echo "=========================================================="
