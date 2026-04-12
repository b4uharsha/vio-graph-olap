#!/usr/bin/env bash
# Provision Kubernetes secrets for Graph OLAP Platform
# Synced from graphsol (HSBC implementation) -- adapt values for your environment
set -euo pipefail

# Configuration -- update these for your environment
NAMESPACE="${NAMESPACE:-graph-olap-platform}"
DB_HOST="${DB_HOST:-0.0.0.0}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-graph-olap-platform}"
DB_USER="${DB_USER:-graph-olap}"

# Logging
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }

# Get Starburst password from: 1) env var, 2) GCP Secret Manager, 3) existing K8s secret
get_starburst_password() {
    # Priority 1: Environment variable
    if [[ -n "${STARBURST_PW:-}" ]]; then
        log_ok "Password: from STARBURST_PW env var"
        echo "$STARBURST_PW"
        return
    fi

    # Priority 2: GCP Secret Manager (if configured)
    if [[ -n "${GCP_PROJECT:-}" ]] && [[ -n "${GCP_SECRET:-}" ]]; then
        local secret_json
        if secret_json=$(gcloud secrets versions access latest --secret="$GCP_SECRET" --project="$GCP_PROJECT" 2>/dev/null); then
            local pw
            pw=$(echo "$secret_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('${GCP_SECRET_KEY:-password}',''))" 2>/dev/null || echo "")
            if [[ -n "$pw" ]]; then
                log_ok "Password: from GCP Secret Manager"
                echo "$pw"
                return
            fi
        fi
    fi

    # Priority 3: Existing K8s secret
    local existing
    existing=$(kubectl get secret export-worker-secrets -n "$NAMESPACE" -o jsonpath='{.data.STARBURST_PASSWORD}' 2>/dev/null | base64 -d 2>/dev/null || echo "")
    if [[ -n "$existing" ]]; then
        log_ok "Password: preserved from existing K8s secret"
        echo "$existing"
        return
    fi

    log_warn "Password: NOT FOUND (export-worker will fail with 401)"
    echo ""
}

main() {
    echo ""
    echo "Creating secrets in namespace: $NAMESPACE"
    echo ""

    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f - >/dev/null

    # Database URL
    local database_url="postgresql+asyncpg://${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

    # Get Starburst password
    local starburst_pw
    starburst_pw=$(get_starburst_password)

    # control-plane-secrets
    kubectl create secret generic control-plane-secrets \
        --namespace="$NAMESPACE" \
        --from-literal=database-url="$database_url" \
        --from-literal=api-internal-token="" \
        --dry-run=client -o yaml | kubectl apply -f - >/dev/null
    log_ok "control-plane-secrets"

    # export-worker-secrets
    kubectl create secret generic export-worker-secrets \
        --namespace="$NAMESPACE" \
        --from-literal=STARBURST_PASSWORD="$starburst_pw" \
        --from-literal=GRAPH_OLAP_INTERNAL_API_KEY="" \
        --dry-run=client -o yaml | kubectl apply -f - >/dev/null
    log_ok "export-worker-secrets"

    # wrapper secrets
    kubectl create secret generic falkordb-wrapper-secret \
        --namespace="$NAMESPACE" \
        --from-literal=internal-api-token="" \
        --dry-run=client -o yaml | kubectl apply -f - >/dev/null
    log_ok "falkordb-wrapper-secret"

    kubectl create secret generic ryugraph-wrapper-secret \
        --namespace="$NAMESPACE" \
        --from-literal=internal-api-token="" \
        --dry-run=client -o yaml | kubectl apply -f - >/dev/null
    log_ok "ryugraph-wrapper-secret"

    echo ""
    if [[ -z "$starburst_pw" ]]; then
        log_info "Fix password: STARBURST_PW='xxx' $0"
        log_info "Then restart: kubectl rollout restart deploy/graph-olap-export-worker -n $NAMESPACE"
        echo ""
    fi
    log_ok "Done"
}

main
