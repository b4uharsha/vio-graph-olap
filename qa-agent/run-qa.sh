#!/usr/bin/env bash
# =============================================================================
# Graph OLAP QA Agent — Nightly Quality Report
# =============================================================================
# Runs lint, type checks, and unit tests across all packages.
# Produces a structured Markdown report at qa-agent/reports/<date>.md
#
# Usage:
#   ./qa-agent/run-qa.sh            # full run
#   ./qa-agent/run-qa.sh --quick    # lint + type checks only (no tests)
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORT_DIR="$ROOT/qa-agent/reports"
DATE=$(date +%Y-%m-%d_%H-%M)
REPORT="$REPORT_DIR/$DATE.md"
QUICK=false

[[ "${1:-}" == "--quick" ]] && QUICK=true

mkdir -p "$REPORT_DIR"

# ── Helpers ──────────────────────────────────────────────────────────────────
PASS=0; FAIL=0; WARN=0; ERRORS=""

section() { echo -e "\n## $1\n" >> "$REPORT"; }
pass()    { PASS=$((PASS+1)); echo "- **PASS** $1" >> "$REPORT"; }
fail()    { FAIL=$((FAIL+1)); echo "- **FAIL** $1" >> "$REPORT"; ERRORS+="  - $1\n"; }
warn()    { WARN=$((WARN+1)); echo "- **WARN** $1" >> "$REPORT"; }

run_check() {
  local label="$1"; shift
  local output
  if output=$("$@" 2>&1); then
    pass "$label"
  else
    fail "$label"
    echo '```' >> "$REPORT"
    echo "$output" | tail -40 >> "$REPORT"
    echo '```' >> "$REPORT"
  fi
}

# ── Packages to check ───────────────────────────────────────────────────────
PACKAGES=(
  "control-plane"
  "export-worker"
  "falkordb-wrapper"
  "ryugraph-wrapper"
  "graph-olap-sdk"
  "graph-olap-schemas"
)

PKG_BASE="$ROOT/graph-packages/packages"

# ── Report Header ────────────────────────────────────────────────────────────
cat > "$REPORT" <<EOF
# Graph OLAP QA Report — $(date '+%B %d, %Y %H:%M')

| Metric | Value |
|--------|-------|
| Branch | $(cd "$ROOT" && git branch --show-current) |
| Commit | $(cd "$ROOT" && git log -1 --format='%h %s') |
| Mode   | $([ "$QUICK" = true ] && echo "Quick (lint+types)" || echo "Full (lint+types+tests)") |
EOF

# ── 1. Ruff Lint ─────────────────────────────────────────────────────────────
section "1. Ruff Lint"
for pkg in "${PACKAGES[@]}"; do
  pkg_dir="$PKG_BASE/$pkg"
  if [ -d "$pkg_dir" ]; then
    if command -v ruff &>/dev/null; then
      run_check "$pkg — ruff check" ruff check "$pkg_dir" --config "$pkg_dir/pyproject.toml"
    else
      warn "$pkg — ruff not installed"
    fi
  fi
done

# ── 2. Ruff Format Check ────────────────────────────────────────────────────
section "2. Ruff Format"
for pkg in "${PACKAGES[@]}"; do
  pkg_dir="$PKG_BASE/$pkg"
  if [ -d "$pkg_dir" ]; then
    if command -v ruff &>/dev/null; then
      run_check "$pkg — ruff format" ruff format --check "$pkg_dir" --config "$pkg_dir/pyproject.toml"
    else
      warn "$pkg — ruff not installed"
    fi
  fi
done

# ── 3. MyPy Type Checks ─────────────────────────────────────────────────────
section "3. MyPy Type Checks"
for pkg in "${PACKAGES[@]}"; do
  pkg_dir="$PKG_BASE/$pkg"
  if [ -d "$pkg_dir" ]; then
    # Find the source directory
    src_dir="$pkg_dir/src"
    [ ! -d "$src_dir" ] && src_dir="$pkg_dir"

    if command -v mypy &>/dev/null; then
      run_check "$pkg — mypy" mypy "$src_dir" --config-file "$pkg_dir/pyproject.toml" --no-error-summary
    else
      warn "$pkg — mypy not installed"
    fi
  fi
done

# ── 4. Unit Tests + Coverage ────────────────────────────────────────────────
if [ "$QUICK" = false ]; then
  section "4. Unit Tests"
  for pkg in "${PACKAGES[@]}"; do
    pkg_dir="$PKG_BASE/$pkg"
    if [ -d "$pkg_dir/tests" ]; then
      run_check "$pkg — pytest unit" \
        python -m pytest "$pkg_dir/tests" \
          -m "not integration and not e2e" \
          --timeout=60 \
          --tb=short \
          -q \
          --no-header \
          --cov="$pkg_dir/src" \
          --cov-report=term-missing:skip-covered \
          --cov-report=json:"$REPORT_DIR/${pkg}-coverage-${DATE}.json" \
          2>/dev/null || true
    else
      warn "$pkg — no tests/ directory"
    fi
  done

  # ── 5. Coverage Summary ──────────────────────────────────────────────────
  section "5. Coverage Summary"
  echo "| Package | Coverage | Status |" >> "$REPORT"
  echo "|---------|----------|--------|" >> "$REPORT"
  for pkg in "${PACKAGES[@]}"; do
    cov_file="$REPORT_DIR/${pkg}-coverage-${DATE}.json"
    if [ -f "$cov_file" ]; then
      pct=$(python3 -c "
import json, sys
with open('$cov_file') as f:
    d = json.load(f)
    print(f\"{d['totals']['percent_covered']:.1f}\")
" 2>/dev/null || echo "N/A")
      if [ "$pct" != "N/A" ]; then
        status="OK"
        pct_int=${pct%.*}
        [ "$pct_int" -lt 70 ] && status="BELOW 70%"
        [ "$pct_int" -lt 50 ] && status="CRITICAL"
        echo "| $pkg | ${pct}% | $status |" >> "$REPORT"
      else
        echo "| $pkg | N/A | — |" >> "$REPORT"
      fi
    else
      echo "| $pkg | — | no coverage data |" >> "$REPORT"
    fi
  done
fi

# ── 6. Git Health ────────────────────────────────────────────────────────────
section "6. Git Health"
cd "$ROOT"
uncommitted=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$uncommitted" -gt 0 ]; then
  warn "$uncommitted uncommitted file(s)"
  git status --porcelain | head -10 >> "$REPORT"
else
  pass "Working tree clean"
fi

stale_branches=$(git branch --merged main 2>/dev/null | grep -v '^\*\|main' | wc -l | tr -d ' ')
if [ "$stale_branches" -gt 0 ]; then
  warn "$stale_branches stale merged branch(es)"
else
  pass "No stale branches"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
section "Summary"
TOTAL=$((PASS + FAIL + WARN))
cat >> "$REPORT" <<EOF
| Result | Count |
|--------|-------|
| PASS   | $PASS |
| FAIL   | $FAIL |
| WARN   | $WARN |
| TOTAL  | $TOTAL |
EOF

if [ "$FAIL" -gt 0 ]; then
  echo -e "\n### Failures\n" >> "$REPORT"
  echo -e "$ERRORS" >> "$REPORT"
  echo "" >> "$REPORT"
  echo "**Overall: FAILING** — $FAIL check(s) need attention." >> "$REPORT"
else
  echo "" >> "$REPORT"
  echo "**Overall: PASSING** — All checks green." >> "$REPORT"
fi

echo -e "\n---\n_Generated by Graph OLAP QA Agent_" >> "$REPORT"

# ── Print to stdout for Claude to capture ────────────────────────────────────
cat "$REPORT"
