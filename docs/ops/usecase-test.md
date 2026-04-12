# Use-Case-ID E2E Validation

## Purpose

Validates that each registered use-case-id produces correct results through
the full pipeline (SDK -> Control Plane -> Wrapper -> Database -> Response).

## Running

```bash
python -m pytest tests/test_usecases.py -v --tb=short
```
