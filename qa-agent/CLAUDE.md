# QA Agent Instructions

This directory contains the Graph OLAP QA Agent — an automated quality assurance runner.

## How it works

`run-qa.sh` runs these checks across all 6 packages in graph-packages/:
1. **Ruff lint** — catches code issues
2. **Ruff format** — enforces consistent style
3. **MyPy** — type safety verification
4. **Pytest unit tests** — with coverage reporting
5. **Coverage summary** — flags packages below 70%
6. **Git health** — uncommitted files, stale branches

## Running

```bash
# Full run (lint + types + tests + coverage)
./qa-agent/run-qa.sh

# Quick run (lint + types only, ~30 seconds)
./qa-agent/run-qa.sh --quick
```

## Reports

Reports are saved as Markdown files in `qa-agent/reports/<date>.md`.

## Scheduled via Claude Code

Use `/schedule` to set up recurring runs. The agent will:
1. Run the QA checks
2. Read the generated report
3. Send you a summary notification on Claude mobile
