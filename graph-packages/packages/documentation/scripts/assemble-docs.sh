#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(cd "$PKG_DIR/../.." && pwd)"
BUILD_DIR="$PKG_DIR/build"

echo "Assembling documentation build..."

# Clean build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy documentation content (preserving structure from document.structure.md)
echo "  Copying docs/ content..."
cp -r "$REPO_ROOT/docs/"* "$BUILD_DIR/"

# Copy MkDocs assets
echo "  Copying stylesheets..."
cp -r "$PKG_DIR/stylesheets" "$BUILD_DIR/"

echo "  Copying javascripts..."
cp -r "$PKG_DIR/javascripts" "$BUILD_DIR/"

# Copy E2E test notebooks
echo "  Copying E2E test notebooks..."
mkdir -p "$BUILD_DIR/tests/e2e"
cp -r "$REPO_ROOT/tests/e2e/notebooks" "$BUILD_DIR/tests/e2e/"

echo "Build assembly complete: $BUILD_DIR"
