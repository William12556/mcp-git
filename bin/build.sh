#!/bin/bash
# mcp-git Build Script
# Bumps the version (pyproject.toml + src/mcp_git/__init__.py), cleans
# previous build artefacts, and creates a wheel + sdist via python -m build.
#
# Usage: ./bin/build.sh

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# Toolchain checks
# ---------------------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
    echo "ERROR: Python 3.9+ required, found $PYTHON_VERSION"
    exit 1
fi

if ! python3 -m build --version >/dev/null 2>&1; then
    echo "ERROR: build module not found"
    echo "Install: python3 -m pip install build"
    exit 1
fi

# ---------------------------------------------------------------------------
# Extract current version from pyproject.toml and prompt for new version
# ---------------------------------------------------------------------------
PREV_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)

if [ -z "$PREV_VERSION" ]; then
    echo "ERROR: Could not extract version from pyproject.toml"
    exit 1
fi

SEMVER_RE='^[0-9]+\.[0-9]+\.[0-9]+$'

while true; do
    read -r -p "Current version: $PREV_VERSION. New version [Enter to keep current]: " VERSION
    if [ -z "$VERSION" ]; then
        VERSION="$PREV_VERSION"
        break
    fi
    if [[ "$VERSION" =~ $SEMVER_RE ]]; then
        break
    fi
    echo "ERROR: Version must be in X.Y.Z format"
done

echo "==> Building mcp-git version $VERSION (was $PREV_VERSION)"

# ---------------------------------------------------------------------------
# Update version in pyproject.toml and src/mcp_git/__init__.py
#
# Both files are patched in place with a targeted regex substitution rather
# than regenerated, so hand-written content (dependencies, docstrings,
# __all__) is preserved untouched.
# ---------------------------------------------------------------------------
echo "==> Updating version in pyproject.toml and src/mcp_git/__init__.py..."
python3 -c "
import re, pathlib

pyproject = pathlib.Path('pyproject.toml')
t = pyproject.read_text()
t = re.sub(r'^version = \"[^\"]+\"', 'version = \"${VERSION}\"', t, count=1, flags=re.MULTILINE)
pyproject.write_text(t)

init_py = pathlib.Path('src/mcp_git/__init__.py')
t = init_py.read_text()
t = re.sub(r'^__version__ = \"[^\"]+\"', '__version__ = \"${VERSION}\"', t, count=1, flags=re.MULTILINE)
init_py.write_text(t)
"

# ---------------------------------------------------------------------------
# Clean previous builds
# ---------------------------------------------------------------------------
echo "==> Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/ src/*.egg-info/

# ---------------------------------------------------------------------------
# Build distribution
# ---------------------------------------------------------------------------
echo "==> Building distribution..."
python3 -m build

# ---------------------------------------------------------------------------
# Verify build artefacts
# ---------------------------------------------------------------------------
WHEEL="$(ls dist/*.whl 2>/dev/null | head -1)"
TARBALL="$(ls dist/*.tar.gz 2>/dev/null | head -1)"

if [ -z "$WHEEL" ]; then
    echo "ERROR: No wheel found in dist/"
    exit 1
fi

if [ -z "$TARBALL" ]; then
    echo "ERROR: No sdist tarball found in dist/"
    exit 1
fi

echo ""
echo "✓ Build successful: version $VERSION"
ls -lh "$WHEEL" "$TARBALL"
echo ""
echo "Install locally:      pip install $WHEEL"
echo "Run test suite first: python -m pytest tests/"
echo "Publish a release:    ./bin/release.sh"
