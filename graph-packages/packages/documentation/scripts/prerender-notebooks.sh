#!/bin/bash
# Pre-render Jupyter notebooks to markdown for faster mkdocs builds
#
# This script converts all .ipynb files to .md files using nbconvert,
# enabling mkdocs to process plain markdown instead of notebooks.
#
# Usage:
#   ./prerender-notebooks.sh <docs_dir>
#
# Example:
#   ./prerender-notebooks.sh /build/docs
#
# The script:
# 1. Finds all .ipynb files in the docs directory
# 2. Converts each to .md using nbconvert (parallel processing)
# 3. Places .md files alongside .ipynb files
# 4. Creates .md files that mkdocs can process directly

set -euo pipefail

DOCS_DIR="${1:-/build/docs}"
PARALLEL_JOBS="${2:-8}"

if [ ! -d "$DOCS_DIR" ]; then
    echo "Error: Directory not found: $DOCS_DIR" >&2
    exit 1
fi

# Find all notebooks (excluding checkpoints)
NOTEBOOKS=$(find "$DOCS_DIR" -name "*.ipynb" -not -path "*/.ipynb_checkpoints/*" -not -name "*.nbconvert.*")
TOTAL=$(echo "$NOTEBOOKS" | wc -l | tr -d ' ')

echo "Pre-rendering $TOTAL notebooks using $PARALLEL_JOBS parallel jobs..."

# Convert notebooks to markdown in parallel
# Using markdown output for mkdocs compatibility
echo "$NOTEBOOKS" | xargs -P "$PARALLEL_JOBS" -I {} sh -c '
    nb="{}"
    md="${nb%.ipynb}.md"
    # Only convert if notebook is newer than markdown
    if [ ! -f "$md" ] || [ "$nb" -nt "$md" ]; then
        python -m nbconvert --to markdown --output-dir "$(dirname "$nb")" "$nb" 2>/dev/null && echo "✓ $(basename "$nb")" || echo "✗ $(basename "$nb")" >&2
    else
        echo "⊘ $(basename "$nb") (cached)"
    fi
'

echo "Done. Notebooks pre-rendered to markdown."
