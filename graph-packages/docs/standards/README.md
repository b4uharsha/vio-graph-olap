# Development Standards

Coding standards, style guides, and best practices for the Graph OLAP Platform.

## Documents

| Document | Purpose |
|----------|---------|
| [python-commenting-standards.md](python-commenting-standards.md) | Docstring conventions, inline comment guidelines, API documentation |
| [python-logging-standards.md](python-logging-standards.md) | Logging levels, structured logging, correlation IDs, sensitive data handling |
| [python-linting-standards.md](python-linting-standards.md) | Ruff configuration, pre-commit hooks, CI enforcement |
| [notebook-design-system.md](notebook-design-system.md) | Jupyter notebook structure, cell organization, output handling |
| [container-build-standards.md](container-build-standards.md) | Multi-stage builds, base image selection, layer optimization, security scanning |

## Reading Order

1. [python-linting-standards.md](python-linting-standards.md) - Start here for code quality enforcement
2. [python-commenting-standards.md](python-commenting-standards.md) - Documentation conventions
3. [python-logging-standards.md](python-logging-standards.md) - Observability standards
4. [container-build-standards.md](container-build-standards.md) - Build and packaging
5. [notebook-design-system.md](notebook-design-system.md) - Notebook authoring

## Related Documentation

- [../governance/](../governance/) - Governance policies
- [../security/](../security/) - Security requirements
- [../process/](../process/) - Development processes

## Implementation Locations

| Standard | Enforcement Location |
|----------|---------------------|
| Python linting | `pyproject.toml`, `.pre-commit-config.yaml` |
| Container builds | `Earthfile`, `infrastructure/helm/` |
| Notebook structure | `jupyter-labs/notebooks/` |
