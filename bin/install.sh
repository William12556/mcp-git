#!/bin/bash
# mcp-git Install Script
# Installs the latest mcp-git release directly from GitHub.
# Does not require cloning the repository.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/William12556/mcp-git/main/bin/install.sh | bash

set -e

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INSTALL_DIR="${MCP_GIT_HOME:-$HOME/.local/share/mcp-git}"
VENV_DIR="$INSTALL_DIR/venv"

# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------
for cmd in python3 curl; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd not found in PATH"
        exit 1
    fi
done

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
    echo "ERROR: Python 3.9+ required, found $PYTHON_VERSION"
    exit 1
fi

# ---------------------------------------------------------------------------
# Resolve latest release tag
# ---------------------------------------------------------------------------
echo "==> Resolving latest release..."
LATEST=$(curl -fsSL https://api.github.com/repos/William12556/mcp-git/releases/latest \
    | grep '"tag_name"' | cut -d'"' -f4)

if [ -z "$LATEST" ]; then
    echo "ERROR: Could not resolve latest release tag"
    exit 1
fi

echo "==> Installing mcp-git ${LATEST}"
echo "==> Install directory: $INSTALL_DIR"

# ---------------------------------------------------------------------------
# Virtual environment
# ---------------------------------------------------------------------------
mkdir -p "$INSTALL_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

# ---------------------------------------------------------------------------
# Install package from GitHub
# ---------------------------------------------------------------------------
echo "==> Cleaning existing installation..."
"$VENV_DIR/bin/pip" uninstall -y mcp-git 2>/dev/null || true

echo "==> Installing from GitHub (${LATEST})..."
"$VENV_DIR/bin/pip" install --upgrade \
    "git+https://github.com/William12556/mcp-git.git@${LATEST}"

# ---------------------------------------------------------------------------
# Version verification
# ---------------------------------------------------------------------------
echo "==> Verifying installation..."
INSTALLED=$("$VENV_DIR/bin/python" -c \
    "import importlib.metadata; print(importlib.metadata.version('mcp-git'))")

echo ""
echo "✓ Installation successful: version $INSTALLED"
echo ""
echo "Add mcp-git to your MCP client configuration with this command:"
echo "  $VENV_DIR/bin/mcp-git"
