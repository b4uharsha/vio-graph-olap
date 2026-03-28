#!/usr/bin/env python3
"""
Convert Jupyter notebooks to markdown for faster MkDocs builds.

This script is used in the notebook-cache Earthly layer to pre-convert
notebooks to markdown. This allows mkdocs to process only markdown files,
significantly reducing build time.

Usage:
    python convert-notebooks.py <docs_dir>

Example:
    python convert-notebooks.py /build/docs

The script will:
1. Find all .ipynb files in the docs directory
2. Convert each to .md using nbconvert
3. Keep both .ipynb and .md files (mkdocs-jupyter needs the .ipynb for source)
"""

import os
import sys
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed


def convert_notebook(notebook_path: Path) -> tuple[Path, bool, str]:
    """Convert a single notebook to markdown.

    Args:
        notebook_path: Path to the .ipynb file

    Returns:
        Tuple of (path, success, message)
    """
    md_path = notebook_path.with_suffix('.md')

    # Skip if markdown already exists and is newer than notebook
    if md_path.exists():
        if md_path.stat().st_mtime >= notebook_path.stat().st_mtime:
            return notebook_path, True, "skipped (up to date)"

    try:
        # Use nbconvert to convert notebook to markdown
        result = subprocess.run(
            [
                'python', '-m', 'nbconvert',
                '--to', 'markdown',
                '--output-dir', str(notebook_path.parent),
                str(notebook_path)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return notebook_path, True, "converted"
        else:
            return notebook_path, False, f"error: {result.stderr}"

    except subprocess.TimeoutExpired:
        return notebook_path, False, "timeout"
    except Exception as e:
        return notebook_path, False, f"exception: {e}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert-notebooks.py <docs_dir>", file=sys.stderr)
        sys.exit(1)

    docs_dir = Path(sys.argv[1])
    if not docs_dir.exists():
        print(f"Error: Directory not found: {docs_dir}", file=sys.stderr)
        sys.exit(1)

    # Find all notebooks
    notebooks = list(docs_dir.rglob("*.ipynb"))

    # Filter out checkpoints
    notebooks = [
        nb for nb in notebooks
        if ".ipynb_checkpoints" not in str(nb)
        and not nb.name.endswith(".nbconvert.ipynb")
    ]

    if not notebooks:
        print("No notebooks found to convert")
        return

    print(f"Converting {len(notebooks)} notebooks...")

    # Convert notebooks in parallel
    converted = 0
    skipped = 0
    errors = 0

    with ProcessPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futures = {executor.submit(convert_notebook, nb): nb for nb in notebooks}

        for future in as_completed(futures):
            path, success, message = future.result()
            if success:
                if "skipped" in message:
                    skipped += 1
                else:
                    converted += 1
                    print(f"  ✓ {path.name}: {message}")
            else:
                errors += 1
                print(f"  ✗ {path.name}: {message}", file=sys.stderr)

    print(f"\nSummary: {converted} converted, {skipped} skipped, {errors} errors")

    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
