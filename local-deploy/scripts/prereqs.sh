#!/usr/bin/env bash
# Check all tools required for local deployment are present.
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC}   $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; FAILED=1; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

FAILED=0

echo "Checking prerequisites..."
echo ""

# Docker
if command -v docker &>/dev/null && docker info &>/dev/null; then
    ok "Docker $(docker version --format '{{.Server.Version}}' 2>/dev/null)"
else
    fail "Docker not running — install from https://docs.docker.com/get-docker/"
fi

# kubectl
if command -v kubectl &>/dev/null; then
    ok "kubectl $(kubectl version --client --short 2>/dev/null || kubectl version --client 2>/dev/null | head -1)"
else
    fail "kubectl not found — install from https://kubernetes.io/docs/tasks/tools/"
fi

# Helm
if command -v helm &>/dev/null; then
    ok "Helm $(helm version --short 2>/dev/null)"
else
    fail "Helm not found — install: brew install helm  or  https://helm.sh/docs/intro/install/"
fi

# A reachable Kubernetes cluster
if kubectl get nodes &>/dev/null; then
    CONTEXT=$(kubectl config current-context 2>/dev/null || echo "unknown")
    NODE_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
    ok "Kubernetes cluster reachable ($NODE_COUNT node(s), context: $CONTEXT)"
else
    fail "No reachable Kubernetes cluster. Start one of:
        OrbStack:        enable in OrbStack Settings → Kubernetes
        Rancher Desktop: enable Kubernetes in preferences
        Docker Desktop:  enable Kubernetes in preferences
        minikube:        minikube start
        kind:            kind create cluster"
fi

# Monorepo root (caller sets MONOREPO_ROOT or we check the default)
MONOREPO_ROOT="${MONOREPO_ROOT:-../graph-olap}"
if [[ -d "$MONOREPO_ROOT/packages/control-plane" ]]; then
    ok "Monorepo found at $MONOREPO_ROOT"
else
    fail "Monorepo not found at '$MONOREPO_ROOT'
        Set MONOREPO_ROOT to the path of the graph-olap repo:
          export MONOREPO_ROOT=/path/to/graph-olap
        or:
          make build MONOREPO_ROOT=/path/to/graph-olap"
fi

echo ""
if [[ "$FAILED" -ne 0 ]]; then
    echo -e "${RED}Prerequisites check FAILED — fix the above issues and re-run.${NC}"
    exit 1
else
    echo -e "${GREEN}All prerequisites OK.${NC}"
fi
