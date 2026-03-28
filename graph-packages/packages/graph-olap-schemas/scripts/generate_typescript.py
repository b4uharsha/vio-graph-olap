#!/usr/bin/env python3
"""Generate TypeScript types from Pydantic JSON schemas.

This script exports JSON schemas from the graph-olap-schemas package and
converts them to TypeScript interfaces using json-schema-to-typescript.

Usage:
    python scripts/generate_typescript.py

Requirements:
    - Node.js and npm must be installed
    - Run 'npm install' in the graph-olap-schemas directory first

Output:
    generated/typescript/
    ├── index.ts                  # Barrel export
    ├── definitions/
    │   ├── PropertyDefinition.ts
    │   ├── NodeDefinition.ts
    │   └── ...
    ├── api/
    │   ├── CreateMappingRequest.ts
    │   └── ...
    └── internal/
        └── ...
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Add parent to path for importing graph_olap_schemas
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_olap_schemas.json_schema import (
    API_COMMON_SCHEMAS,
    API_INTERNAL_SCHEMAS,
    API_RESOURCE_SCHEMAS,
    DEFINITION_SCHEMAS,
    get_schema,
)


def check_node_installed() -> bool:
    """Check if Node.js and npx are available."""
    try:
        subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def convert_schema_to_typescript(
    schema_path: Path,
    output_path: Path,
    type_name: str,
) -> bool:
    """Convert a single JSON schema file to TypeScript.

    Args:
        schema_path: Path to JSON schema file
        output_path: Path to write TypeScript file
        type_name: Name for the root type

    Returns:
        True if conversion succeeded
    """
    try:
        subprocess.run(
            [
                "npx",
                "json-schema-to-typescript",
                str(schema_path),
                "-o",
                str(output_path),
                "--bannerComment",
                "",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error converting {type_name}: {e.stderr}")
        return False


def generate_category_types(
    schemas: dict[str, type],
    temp_dir: Path,
    output_dir: Path,
    category: str,
) -> list[str]:
    """Generate TypeScript types for a schema category.

    Args:
        schemas: Dictionary mapping type name to Pydantic model
        temp_dir: Temporary directory for JSON schema files
        output_dir: Directory to write TypeScript files
        category: Category name for subdirectory

    Returns:
        List of successfully generated type names
    """
    category_dir = output_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)

    schema_dir = temp_dir / category
    schema_dir.mkdir(parents=True, exist_ok=True)

    generated_types = []

    for name, model in schemas.items():
        # Export JSON schema
        schema = get_schema(model)
        schema_path = schema_dir / f"{name}.json"
        schema_path.write_text(json.dumps(schema, indent=2))

        # Convert to TypeScript
        ts_path = category_dir / f"{name}.ts"
        if convert_schema_to_typescript(schema_path, ts_path, name):
            generated_types.append(name)
            print(f"  Generated {category}/{name}.ts")
        else:
            print(f"  Failed to generate {category}/{name}.ts")

    return generated_types


def generate_barrel_export(
    output_dir: Path,
    categories: dict[str, list[str]],
) -> None:
    """Generate index.ts barrel export file.

    Uses explicit named exports to avoid conflicts from helper type aliases
    that are duplicated across schema files (e.g., Name, Status, Description).

    Args:
        output_dir: Root output directory
        categories: Dictionary mapping category to list of type names
    """
    lines = [
        "/**",
        " * Graph OLAP Platform TypeScript Types",
        " *",
        " * Auto-generated from Pydantic schemas. Do not edit manually.",
        " * Regenerate with: python scripts/generate_typescript.py",
        " */",
        "",
    ]

    for category, types in categories.items():
        if types:
            lines.append(f"// {category.replace('_', ' ').title()}")
            for type_name in sorted(types):
                # Use explicit named export to avoid conflicts from helper types
                lines.append(f"export {{ {type_name} }} from './{category}/{type_name}';")
            lines.append("")

    index_path = output_dir / "index.ts"
    index_path.write_text("\n".join(lines))
    print(f"\nGenerated barrel export: {index_path}")


def main() -> int:
    """Generate TypeScript types from all schemas."""
    print("Generating TypeScript types from Pydantic schemas...")
    print()

    # Check prerequisites
    if not check_node_installed():
        print("Error: Node.js and npx are required.")
        print("Install Node.js from https://nodejs.org/")
        return 1

    # Install npm dependencies if needed
    project_dir = Path(__file__).parent.parent
    package_json = project_dir / "package.json"
    if not package_json.exists():
        print("Error: package.json not found. Run from graph-olap-schemas directory.")
        return 1

    node_modules = project_dir / "node_modules"
    if not node_modules.exists():
        print("Installing npm dependencies...")
        subprocess.run(["npm", "install"], cwd=project_dir, check=True)
        print()

    # Set up directories
    output_dir = project_dir / "generated" / "typescript"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Clear existing generated files
    for item in output_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    # Generate types using temp directory for JSON schemas
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        categories = {}

        print("Generating definition types...")
        categories["definitions"] = generate_category_types(
            DEFINITION_SCHEMAS, temp_path, output_dir, "definitions"
        )

        print("\nGenerating API common types...")
        categories["api_common"] = generate_category_types(
            API_COMMON_SCHEMAS, temp_path, output_dir, "api_common"
        )

        print("\nGenerating API resource types...")
        categories["api_resources"] = generate_category_types(
            API_RESOURCE_SCHEMAS, temp_path, output_dir, "api_resources"
        )

        print("\nGenerating API internal types...")
        categories["api_internal"] = generate_category_types(
            API_INTERNAL_SCHEMAS, temp_path, output_dir, "api_internal"
        )

    # Generate barrel export
    generate_barrel_export(output_dir, categories)

    # Summary
    total = sum(len(types) for types in categories.values())
    print(f"\nGenerated {total} TypeScript type files")
    print(f"Output directory: {output_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
