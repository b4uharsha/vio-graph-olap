#!/usr/bin/env python3
"""
Fast documentation build - pre-renders notebooks then runs mkdocs.

This script:
1. Pre-renders all notebooks to HTML in parallel (~15s for 127 notebooks)
2. Creates a temporary mkdocs config that references .html files instead of .ipynb
3. Runs mkdocs build (fast, ~15s for markdown only)

Total build time: ~30s instead of ~110s

Usage:
    python build-fast.py [--parallel JOBS]

Environment:
    PARALLEL_JOBS: Number of parallel jobs (default: 8)
"""

import os
import re
import sys
import yaml
import shutil
import tempfile
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed


def convert_notebook(notebook_path: Path, docs_dir: Path) -> tuple[Path, bool, str]:
    """Convert a notebook to HTML using nbconvert."""
    try:
        # Output HTML next to the notebook
        result = subprocess.run(
            [
                'python', '-m', 'nbconvert',
                '--to', 'html',
                '--template', 'classic',
                '--output-dir', str(notebook_path.parent),
                str(notebook_path)
            ],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return notebook_path, True, "converted"
        else:
            return notebook_path, False, f"error: {result.stderr[:200]}"
    except Exception as e:
        return notebook_path, False, f"exception: {e}"


def update_nav_entry(entry, ipynb_to_html: dict):
    """Recursively update nav entries to reference .html instead of .ipynb."""
    if isinstance(entry, str):
        if entry.endswith('.ipynb'):
            return ipynb_to_html.get(entry, entry.replace('.ipynb', '.html'))
        return entry
    elif isinstance(entry, dict):
        return {k: update_nav_entry(v, ipynb_to_html) for k, v in entry.items()}
    elif isinstance(entry, list):
        return [update_nav_entry(item, ipynb_to_html) for item in entry]
    return entry


def main():
    parallel_jobs = int(os.environ.get('PARALLEL_JOBS', '8'))
    docs_dir = Path('/build/docs')
    mkdocs_config = Path('/build/mkdocs.yml')

    print(f"Fast documentation build with {parallel_jobs} parallel jobs")

    # Step 1: Find all notebooks (should already be pre-rendered by notebook-prerender layer)
    notebooks = list(docs_dir.rglob("*.ipynb"))
    notebooks = [nb for nb in notebooks
                 if ".ipynb_checkpoints" not in str(nb)
                 and not nb.name.endswith(".nbconvert.ipynb")]

    # Check if HTML files already exist (pre-rendered)
    existing_html = sum(1 for nb in notebooks if nb.with_suffix('.html').exists())

    if existing_html < len(notebooks):
        print(f"\n1. Pre-rendering {len(notebooks) - existing_html} notebooks (found {existing_html} cached)...")

        # Convert only missing notebooks
        ipynb_to_html = {}
        with ProcessPoolExecutor(max_workers=parallel_jobs) as executor:
            futures = {}
            for nb in notebooks:
                if not nb.with_suffix('.html').exists():
                    futures[executor.submit(convert_notebook, nb, docs_dir)] = nb
                else:
                    rel_path = str(nb.relative_to(docs_dir))
                    ipynb_to_html[rel_path] = rel_path.replace('.ipynb', '.html')

            for future in as_completed(futures):
                path, success, msg = future.result()
                rel_path = str(path.relative_to(docs_dir))
                html_path = rel_path.replace('.ipynb', '.html')
                if success:
                    ipynb_to_html[rel_path] = html_path
                    print(f"  ✓ {path.name}")
                else:
                    print(f"  ✗ {path.name}: {msg}", file=sys.stderr)
    else:
        print(f"\n1. Using {existing_html} pre-rendered notebooks (all cached)")
        ipynb_to_html = {
            str(nb.relative_to(docs_dir)): str(nb.relative_to(docs_dir)).replace('.ipynb', '.html')
            for nb in notebooks
        }

    print(f"\n   Total notebooks: {len(ipynb_to_html)}")

    # Step 2: Create modified mkdocs config using string replacement
    # (avoid YAML parsing issues with Python tags)
    print("\n2. Creating optimized mkdocs config...")

    with open(mkdocs_config) as f:
        content = f.read()

    # Remove mkdocs-jupyter plugin section using regex
    import re
    # Remove the mkdocs-jupyter plugin entry
    content = re.sub(
        r'  - mkdocs-jupyter:.*?(?=\n  -|\nmarkdown_extensions:|\n\w)',
        '',
        content,
        flags=re.DOTALL
    )

    # Replace .ipynb references with .html in nav
    for ipynb_path, html_path in ipynb_to_html.items():
        content = content.replace(ipynb_path, html_path)

    # Write modified config
    modified_config = Path('/build/mkdocs-fast.yml')
    with open(modified_config, 'w') as f:
        f.write(content)

    print(f"   Wrote {modified_config}")

    # Step 3: Run mkdocs build with modified config
    print("\n3. Building documentation site...")

    result = subprocess.run(
        ['mkdocs', 'build', '-f', str(modified_config)],
        cwd='/build',
        capture_output=False
    )

    if result.returncode != 0:
        print("\n✗ Build failed", file=sys.stderr)
        sys.exit(1)

    print("\n✓ Fast build complete!")


if __name__ == "__main__":
    main()
