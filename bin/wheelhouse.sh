#!/bin/bash
# mcp-git Windows Wheelhouse Script
# Bundles the mcp-git wheel from dist/ and all runtime dependency wheels for
# Windows (CPython 3.13, AMD64) into a single zip for offline installation
# with: pip install --no-index --find-links <folder> mcp-git
# Requires: dist/ built via build.sh, network access to PyPI.
#
# Usage: ./bin/wheelhouse.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# Target
#
# pip download evaluates sys_platform / platform_system markers against the
# build host, not the target, so Windows-only runtime dependencies are listed
# explicitly: pywin32 (required by mcp), colorama (required by click).
# ---------------------------------------------------------------------------
TARGET_PLATFORM="win_amd64"
TARGET_PYTHON="3.13"
TARGET_TAG="py313"
WINDOWS_EXTRAS=("pywin32>=311" "colorama")

# ---------------------------------------------------------------------------
# Version and wheel
# ---------------------------------------------------------------------------
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)

if [ -z "$VERSION" ]; then
    echo "ERROR: Could not extract version from pyproject.toml"
    exit 1
fi

WHEEL="$(ls dist/mcp_git-"${VERSION}"-*.whl 2>/dev/null | head -1)"

if [ -z "$WHEEL" ]; then
    echo "ERROR: No wheel for version $VERSION found in dist/"
    echo "Run: ./bin/build.sh"
    exit 1
fi

# ---------------------------------------------------------------------------
# Download dependency wheels
# ---------------------------------------------------------------------------
BUNDLE="mcp-git-${VERSION}-${TARGET_PLATFORM}-${TARGET_TAG}"
STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGE_DIR"' EXIT
mkdir "$STAGE_DIR/$BUNDLE"

echo "==> Downloading wheels for $TARGET_PLATFORM, Python $TARGET_PYTHON..."
python3 -m pip download \
    --dest "$STAGE_DIR/$BUNDLE" \
    --only-binary=:all: \
    --platform "$TARGET_PLATFORM" \
    --python-version "$TARGET_PYTHON" \
    --implementation cp \
    "$WHEEL" "${WINDOWS_EXTRAS[@]}"

# ---------------------------------------------------------------------------
# Package
# ---------------------------------------------------------------------------
ZIP="$PROJECT_ROOT/dist/${BUNDLE}.zip"
rm -f "$ZIP"
(cd "$STAGE_DIR" && python3 -m zipfile -c "$ZIP" "$BUNDLE")

echo ""
echo "✓ Wheelhouse built: $(ls "$STAGE_DIR/$BUNDLE" | wc -l | tr -d ' ') wheels"
ls -lh "$ZIP"
echo ""
echo "Publish a release:    ./bin/release.sh"
