# Graph OLAP Notebooks

Interactive Jupyter notebooks for learning and using Graph OLAP.

## Structure

```
docs/notebooks/
├── tutorials/           # Step-by-step learning tracks
│   ├── 00-start-here/   # Welcome and quick start
│   ├── 01-fundamentals/ # SDK basics
│   ├── 02-cypher/       # Query language
│   ├── 03-algorithms/   # Graph algorithms
│   ├── 04-admin-ops/    # Administration
│   └── 05-advanced/     # Advanced topics
├── reference/           # API documentation
│   ├── sdk/             # SDK class reference
│   └── algorithms/      # Algorithm reference
└── examples/            # Runnable examples
    └── use-cases/       # Real-world scenarios
```

## Getting Started

1. Open `_welcome.ipynb` in JupyterLab
2. Follow the **Tutorials** track for guided learning
3. Use **Reference** for API documentation
4. Explore **Examples** for real-world use cases

## Learning Path

| Track | Focus | Time |
|-------|-------|------|
| 00-start-here | Quick introduction | 10 min |
| 01-fundamentals | SDK basics | 2 hours |
| 02-cypher | Query language | 2 hours |
| 03-algorithms | Graph algorithms | 3 hours |
| 04-admin-ops | Administration | 45 min |
| 05-advanced | Advanced topics | 1.5 hours |

## Running Notebooks

These notebooks are designed to run in the Graph OLAP JupyterHub environment, which provides:
- Pre-configured SDK connection
- Access to the control plane
- Custom CSS styling

## Development

- Notebooks use a custom design system (see `assets/styles/notebook.css`)
- Follow the [Notebook Design System](../standards/notebook-design-system.md) for styling
