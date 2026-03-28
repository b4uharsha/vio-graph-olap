#!/usr/bin/env bash
# Deploy the full Graph OLAP stack to a local Kubernetes cluster.
#
# Deploys in two phases:
#   1. local-infra  — PostgreSQL + extension-server + Kubernetes secrets
#   2. graph-olap   — control-plane + export-worker (umbrella Helm chart)
#
# Usage:
#   MONOREPO_ROOT=../graph-olap NAMESPACE=graph-olap-local ./deploy.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"

# If MONOREPO_ROOT is not set, or set to a non-existent path, try the default sibling path
if [[ -z "${MONOREPO_ROOT:-}" ]] || [[ ! -d "$MONOREPO_ROOT" ]]; then
    MONOREPO_ROOT="$LOCAL_DEPLOY_DIR/../graph-olap"
fi

MONOREPO_ROOT="$(cd "$MONOREPO_ROOT" && pwd)"
NAMESPACE="${NAMESPACE:-graph-olap-local}"

HELM_CHARTS="$LOCAL_DEPLOY_DIR/helm/charts"
LOCAL_INFRA_CHART="$HELM_CHARTS/local-infra"
APP_CHART="$HELM_CHARTS/graph-olap"
JUPYTER_CHART="$HELM_CHARTS/jupyter-labs"
VALUES_FILE="$LOCAL_DEPLOY_DIR/helm/values-local.yaml"
K8S_DIR="$LOCAL_DEPLOY_DIR/k8s"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

validate() {
    if [[ ! -d "$LOCAL_INFRA_CHART" ]]; then
        error "local-infra chart not found at: $LOCAL_INFRA_CHART"
        exit 1
    fi

    if [[ ! -d "$APP_CHART" ]]; then
        error "graph-olap chart not found at: $APP_CHART"
        exit 1
    fi

    if [[ ! -f "$VALUES_FILE" ]]; then
        error "Values file not found: $VALUES_FILE"
        exit 1
    fi

    # Verify images exist in at least one local Docker daemon.
    # Check both the active daemon and OrbStack's daemon (they may differ).
    local orbstack_sock="$HOME/.orbstack/run/docker.sock"
    local missing=0
    for img in control-plane:latest export-worker:latest falkordb-wrapper:latest ryugraph-wrapper:latest documentation:latest jupyter-labs:latest; do
        if ! docker inspect "$img" &>/dev/null && \
           ! docker -H "unix://$orbstack_sock" inspect "$img" &>/dev/null 2>/dev/null; then
            error "Image not found: $img — run 'make build' first"
            ((missing++)) || true
        fi
    done
    [[ "$missing" -eq 0 ]] || exit 1

    # Ensure all images are loaded into OrbStack's daemon (K8s uses it)
    if [[ -S "$orbstack_sock" ]]; then
        info "Syncing images to OrbStack daemon..."
        for img in control-plane:latest export-worker:latest falkordb-wrapper:latest ryugraph-wrapper:latest documentation:latest jupyter-labs:latest e2e-tests:latest ryugraph-wrapper:local falkordb-wrapper:local; do
            if docker inspect "$img" &>/dev/null && \
               ! docker -H "unix://$orbstack_sock" inspect "$img" &>/dev/null 2>/dev/null; then
                info "  Loading $img → OrbStack"
                docker save "$img" | docker -H "unix://$orbstack_sock" load || true
            fi
        done
    fi
}

# ---------------------------------------------------------------------------
# Phase 1: local-infra (postgres + extension-server + secrets)
# ---------------------------------------------------------------------------

ensure_nginx_ingress() {
    info "Ensuring nginx ingress controller..."

    if kubectl get deployment ingress-nginx-controller -n ingress-nginx &>/dev/null; then
        ok "nginx ingress controller already installed"
        return 0
    fi

    # Add repo explicitly to avoid stale/missing cache issues
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 2>/dev/null || true
    helm repo update ingress-nginx

    helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.service.type=NodePort \
        --set controller.service.nodePorts.http=30081 \
        --set controller.service.nodePorts.https=30443 \
        --wait \
        --timeout 3m

    ok "nginx ingress controller installed (NodePort 30081)"
}

deploy_infra() {
    info "Phase 1/3: Deploying local-infra (PostgreSQL + extension-server)..."

    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f - 2>/dev/null

    # Create a placeholder GCP SA key secret so export-worker pod can start.
    # Replace with a real service account key to enable GCS access:
    #   kubectl create secret generic gcp-sa-key \
    #     --from-file=key.json=/path/to/sa-key.json \
    #     -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    if [[ -n "${GCP_SA_KEY_JSON:-}" ]]; then
        info "Creating gcp-sa-key secret from GCP_SA_KEY_JSON..."
        echo "$GCP_SA_KEY_JSON" > /tmp/gcs-sa-key.json
        kubectl create secret generic gcp-sa-key \
            --from-file=key.json=/tmp/gcs-sa-key.json \
            -n "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
        rm -f /tmp/gcs-sa-key.json
        ok "GCP SA key secret created (real GCS access enabled)"
    elif ! kubectl get secret gcp-sa-key -n "$NAMESPACE" &>/dev/null; then
        info "Creating placeholder gcp-sa-key secret (GCS access disabled)..."
        # Placeholder must have a valid 'type' field — google.auth rejects bare {}
        # authorized_user type requires no RSA key and won't crash at load time.
        # STORAGE_EMULATOR_HOST routes all GCS traffic to fake-gcs-local anyway.
        kubectl create secret generic gcp-sa-key \
            --from-literal=key.json='{"type":"authorized_user","client_id":"local","client_secret":"local","refresh_token":"local"}' \
            -n "$NAMESPACE"
        warn "GCS routed to fake-gcs-local (STORAGE_EMULATOR_HOST=http://fake-gcs-local:4443)"
    else
        info "gcp-sa-key secret already exists — skipping"
    fi

    helm upgrade --install local-infra "$LOCAL_INFRA_CHART" \
        --namespace "$NAMESPACE" \
        --values "$LOCAL_INFRA_CHART/values-local.yaml" \
        --wait \
        --timeout 3m

    ok "local-infra deployed"
}

# ---------------------------------------------------------------------------
# Phase 2: app stack (control-plane + export-worker)
# ---------------------------------------------------------------------------

deploy_app() {
    info "Phase 2/3: Deploying application stack..."

    # Starburst credentials — export-worker cannot query without them.
    # Control-plane starts fine with empty values; export job execution will fail.
    local starburst_user="${STARBURST_USER:-}"
    local starburst_password="${STARBURST_PASSWORD:-}"

    if [[ -z "$starburst_user" ]]; then
        warn "STARBURST_USER not set — export jobs will fail but core API will work."
        warn "Set STARBURST_USER and STARBURST_PASSWORD to enable export jobs."
        starburst_user="not-configured"
        starburst_password="not-configured"
    else
        ok "Starburst credentials found ($starburst_user)"
    fi

    # Update Helm chart dependencies (sub-charts must be resolved)
    info "Updating Helm chart dependencies..."
    helm dependency update "$APP_CHART" >/dev/null 2>&1 || true

    helm upgrade --install graph-olap "$APP_CHART" \
        --namespace "$NAMESPACE" \
        --values "$VALUES_FILE" \
        --set "control-plane.config.wrapper.image=ryugraph-wrapper:local" \
        --set "control-plane.config.wrapper.falkordbImage=falkordb-wrapper:local" \
        --set "control-plane.config.k8s.namespace=$NAMESPACE" \
        --set "control-plane.env.GRAPH_OLAP_STARBURST_USER=$starburst_user" \
        --set "control-plane.env.GRAPH_OLAP_STARBURST_PASSWORD=$starburst_password" \
        --set "export-worker.config.starburst.user=$starburst_user" \
        --set "exportWorkerSecrets.starburstPassword=$starburst_password" \
        --wait \
        --timeout 5m

    ok "Application stack deployed"
}

# ---------------------------------------------------------------------------
# Phase 3: ingress routes
# ---------------------------------------------------------------------------

deploy_ingress_routes() {
    info "Phase 3/4: Applying ingress routes..."
    kubectl apply -f "$K8S_DIR/control-plane-rbac.yaml"
    kubectl apply -f "$K8S_DIR/control-plane-ingress.yaml" 2>/dev/null || true
    # Deploy fake-gcs-server for local GCS emulation (used by export-worker)
    kubectl apply -f "$K8S_DIR/fake-gcs-server.yaml" 2>/dev/null || true
    # Deploy local setup docs site (port 30082)
    kubectl apply -f "$K8S_DIR/local-docs.yaml" 2>/dev/null || true
    ok "Ingress routes applied"
}

init_fake_gcs_bucket() {
    info "Initializing fake-GCS bucket 'graph-olap-local-dev'..."

    # Wait up to 30s for the fake-gcs pod to be Running
    local pod=""
    local i
    for i in $(seq 1 15); do
        pod=$(kubectl get pods -n "$NAMESPACE" -l app=fake-gcs-local \
            --no-headers 2>/dev/null | grep Running | awk '{print $1}' | head -1 || true)
        [[ -n "$pod" ]] && break
        sleep 2
    done

    if [[ -z "$pod" ]]; then
        warn "fake-gcs pod not ready — bucket will be created on first notebook run"
        return 0
    fi

    # Create bucket via GCS JSON API (409 = already exists, both are fine)
    local status
    status=$(kubectl exec -n "$NAMESPACE" "$pod" -- \
        wget -q -S -O /dev/null \
             --post-data='{"name":"graph-olap-local-dev"}' \
             --header='Content-Type: application/json' \
             'http://localhost:4443/storage/v1/b' 2>&1 \
        | { grep "HTTP/" || true; } | awk '{print $2}' | head -1 || echo "0")

    if [[ "$status" == "200" || "$status" == "201" || "$status" == "409" ]]; then
        ok "GCS bucket 'graph-olap-local-dev' ready (status $status)"
    else
        warn "Bucket creation returned status $status — notebooks will create it on demand"
    fi
}

# ---------------------------------------------------------------------------
# Phase 4: jupyter-labs
# ---------------------------------------------------------------------------

deploy_jupyter() {
    if [[ ! -d "$JUPYTER_CHART" ]]; then
        warn "jupyter-labs chart not found at $JUPYTER_CHART — skipping."
        return 0
    fi

    info "Phase 4/4: Deploying jupyter-labs..."

    helm dependency update "$JUPYTER_CHART" >/dev/null 2>&1 || true

    helm upgrade --install jupyter-labs "$JUPYTER_CHART" \
        --namespace "$NAMESPACE" \
        --set "image.repository=jupyter-labs" \
        --set "image.tag=latest" \
        --set "image.pullPolicy=Never" \
        --set "env.GRAPH_OLAP_URL=http://control-plane:8080" \
        --wait \
        --timeout 3m

    ok "jupyter-labs deployed"
}

# ---------------------------------------------------------------------------
# Phase 5: copy demo notebook into Jupyter pod
# ---------------------------------------------------------------------------

copy_demo_notebooks() {
    info "Phase 5/5: Copying demo notebooks to Jupyter pod..."

    local jupyter_pod
    jupyter_pod=$(kubectl get pods -n "$NAMESPACE" -l app=jupyter-labs \
        --no-headers -o custom-columns=':metadata.name' 2>/dev/null | head -1)

    if [[ -z "$jupyter_pod" ]]; then
        warn "Jupyter pod not found — skipping notebook copy"
        return 0
    fi

    local notebooks=(
        "00-cleanup.ipynb"
        "01-movie-graph-demo.ipynb"
        "02-music-graph-demo.ipynb"
        "03-ecommerce-graph-demo.ipynb"
        "04-ipl-t20-graph-demo.ipynb"
        "05-algorithms-demo.ipynb"
    )

    for nb in "${notebooks[@]}"; do
        local src="$LOCAL_DEPLOY_DIR/notebooks/$nb"
        if [[ -f "$src" ]]; then
            kubectl cp "$src" "$NAMESPACE/$jupyter_pod:/home/jovyan/work/$nb"
            ok "  Copied: $nb"
        fi
    done

    # Copy the SDK helper module so all notebooks can import it
    local sdk="$LOCAL_DEPLOY_DIR/notebooks/graph_olap_sdk.py"
    if [[ -f "$sdk" ]]; then
        kubectl cp "$sdk" "$NAMESPACE/$jupyter_pod:/home/jovyan/work/graph_olap_sdk.py"
        ok "  Copied: graph_olap_sdk.py"
    fi

    ok "Demo notebooks ready: http://localhost:30081/jupyter/lab"
}

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

health_check() {
    info "Waiting for API to become ready..."

    local api_url="http://localhost:30081"
    local retries=30

    for i in $(seq 1 $retries); do
        if curl -sf "$api_url/health" >/dev/null 2>&1; then
            ok "API healthy: $api_url"
            return 0
        fi
        echo -n "."
        sleep 2
    done

    echo ""
    warn "API not reachable at $api_url after ${retries} retries."
    warn "Services may still be starting. Run: make status"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

main() {
    echo "================================================"
    echo " Graph OLAP — Local Deployment"
    echo "================================================"
    echo " Monorepo:  $MONOREPO_ROOT"
    echo " Namespace: $NAMESPACE"
    echo ""

    validate
    ensure_nginx_ingress
    echo ""
    deploy_infra
    echo ""
    deploy_app
    echo ""
    deploy_ingress_routes
    echo ""
    init_fake_gcs_bucket
    echo ""
    deploy_jupyter
    echo ""
    copy_demo_notebooks
    echo ""
    health_check

    echo ""
    echo "================================================"
    ok "Deployment complete!"
    echo "================================================"
    echo ""
    echo "  Documentation:      http://localhost:30081"
    echo "  Jupyter Labs:       http://localhost:30081/jupyter/lab"
    echo "  Control Plane API:  http://localhost:30081/api/..."
    echo "  Health endpoint:    http://localhost:30081/health"
    echo ""
    echo "  make status         — check pod health"
    echo "  make logs SVC=control-plane — tail logs"
    echo "  make teardown       — remove everything"
}

main
