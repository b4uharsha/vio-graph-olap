# Platform Documentation

Custom documentation for the Graph OLAP Platform that extends or supplements upstream Ryugraph docs.

## Purpose

- Document platform-specific configurations, workarounds, and guides
- Follows the same structure as upstream docs for consistency
- Contains our additions, corrections, and platform-specific content

## Structure

```
platform/
├── depot-dev.mdx         # depot.dev configuration for native cloud builds
├── extensions/           # Extension-related platform docs
│   └── arm64-workaround.mdx
└── README.md             # This file
```

## Relationship to Reference Docs

| Directory | Content | Modifiable? |
|-----------|---------|-------------|
| `reference/ryugraph-v25.9/` | Upstream snapshot | NO - read-only |
| `platform/` | Our custom docs | YES - we own this |

## When to Add Docs Here

1. **Workarounds** for upstream bugs (e.g., ARM64 extension issue)
2. **Platform-specific** configurations not in upstream
3. **Supplementary** guides for our specific use cases
4. **Corrections** to upstream docs (document here, don't modify snapshots)

## Format

Use `.mdx` format following the same conventions as upstream Ryugraph docs:
- Frontmatter with `title` and `description`
- Starlight/Astro-compatible admonitions (:::note, :::caution, :::danger)
