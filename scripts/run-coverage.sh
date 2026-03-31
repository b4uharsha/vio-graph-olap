#!/usr/bin/env bash
# Run test coverage across all packages and produce a summary report.
# Usage: ./scripts/run-coverage.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGES_DIR="$ROOT/graph-packages/packages"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "═══════════════════════════════════════════════════════════════"
echo "  Graph OLAP — Test Coverage Report"
echo "═══════════════════════════════════════════════════════════════"
echo ""

TOTAL_PASS=0
TOTAL_FAIL=0
RESULTS=()

for pkg_dir in "$PACKAGES_DIR"/*/; do
    pkg_name=$(basename "$pkg_dir")

    # Skip non-Python packages
    if [[ ! -f "$pkg_dir/pyproject.toml" ]]; then
        continue
    fi

    # Skip packages without tests
    if [[ ! -d "$pkg_dir/tests" ]]; then
        continue
    fi

    echo -e "${YELLOW}▶ $pkg_name${NC}"
    cd "$pkg_dir"

    if python -m pytest tests/unit/ --no-header -q 2>/dev/null; then
        TOTAL_PASS=$((TOTAL_PASS + 1))
        RESULTS+=("${GREEN}✓ $pkg_name${NC}")
    else
        TOTAL_FAIL=$((TOTAL_FAIL + 1))
        RESULTS+=("${RED}✗ $pkg_name${NC}")
    fi
    echo ""
done

echo "═══════════════════════════════════════════════════════════════"
echo "  Summary"
echo "═══════════════════════════════════════════════════════════════"
for r in "${RESULTS[@]}"; do
    echo -e "  $r"
done
echo ""
echo -e "  Passed: ${GREEN}$TOTAL_PASS${NC}  Failed: ${RED}$TOTAL_FAIL${NC}"
echo "═══════════════════════════════════════════════════════════════"
