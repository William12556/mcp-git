#!/bin/bash
# mcp-git Release Script
# Creates a versioned GitHub release with dist artefacts.
# Requires: gh CLI authenticated, dist/ built via build.sh
#
# Usage: ./bin/release.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# gh CLI check
# ---------------------------------------------------------------------------
if ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: gh CLI not found"
    echo "Install: https://cli.github.com"
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "ERROR: gh not authenticated"
    echo "Run: gh auth login"
    exit 1
fi

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)

if [ -z "$VERSION" ]; then
    echo "ERROR: Could not extract version from pyproject.toml"
    exit 1
fi

TAG="v${VERSION}"

# ---------------------------------------------------------------------------
# Dist artefacts
# ---------------------------------------------------------------------------
WHEEL="$(ls dist/*.whl 2>/dev/null | head -1)"
TARBALL="$(ls dist/*.tar.gz 2>/dev/null | head -1)"

if [ -z "$WHEEL" ]; then
    echo "ERROR: No wheel found in dist/"
    echo "Run: ./bin/build.sh"
    exit 1
fi

if [ -z "$TARBALL" ]; then
    echo "ERROR: No sdist tarball found in dist/"
    echo "Run: ./bin/build.sh"
    exit 1
fi

# ---------------------------------------------------------------------------
# Version sanity check: dist artefacts must match pyproject.toml
# ---------------------------------------------------------------------------
if [[ "$(basename "$WHEEL")" != *"${VERSION}"* ]]; then
    echo "ERROR: dist/ artefacts do not match pyproject.toml version $VERSION"
    echo "Found: $(basename "$WHEEL")"
    echo "Run: ./bin/build.sh"
    exit 1
fi

# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------
if command -v pytest >/dev/null 2>&1; then
    echo "==> Running test suite..."
    pytest tests/
else
    echo "WARNING: pytest not found on PATH — skipping pre-release test run"
    read -r -p "Continue without running tests? [y/N] " CONFIRM
    case "$CONFIRM" in
        [yY]) ;;
        *) echo "Aborted."; exit 1 ;;
    esac
fi

# ---------------------------------------------------------------------------
# Uncommitted changes warning
# ---------------------------------------------------------------------------
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "WARNING: Uncommitted changes in working tree"
    read -r -p "Continue? [y/N] " CONFIRM
    case "$CONFIRM" in
        [yY]) ;;
        *) echo "Aborted."; exit 1 ;;
    esac
fi

# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------
echo "==> Creating release $TAG"

gh release create "$TAG" \
    --title "$TAG" \
    --notes "mcp-git $TAG" \
    --latest \
    "$WHEEL" \
    "$TARBALL"

echo ""
echo "✓ Release $TAG published"
