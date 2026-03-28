#!/usr/bin/env bash
# Remove all Graph OLAP local deployment resources.
set -euo pipefail

NAMESPACE="${1:-graph-olap-local}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC}    $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
info() { echo -e "${CYAN}[INFO]${NC}  $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALUES_FILE="$SCRIPT_DIR/../helm/values-local.yaml"
ENV_FILE="$SCRIPT_DIR/../.env"

echo "Removing Graph OLAP local deployment (namespace: $NAMESPACE)..."
echo ""

# ---------------------------------------------------------------------------
# Detect GCS bucket — check extraEnv first, then config section
# ---------------------------------------------------------------------------
detect_gcs_bucket() {
    local bucket=""
    if [[ -f "$VALUES_FILE" ]]; then
        # Prefer the actual runtime bucket from extraEnv (what export-worker uses)
        bucket=$(grep -A1 'name: GCS_BUCKET' "$VALUES_FILE" 2>/dev/null \
            | { grep 'value:' || true; } | awk '{print $2}' | tr -d '"' | head -1 || true)
        # Fall back to config.gcs.bucket if not a placeholder
        if [[ -z "$bucket" || "$bucket" == "your-gcs-bucket" ]]; then
            bucket=$({ grep 'bucket:' "$VALUES_FILE" 2>/dev/null || true; } \
                | head -1 | awk '{print $2}' | tr -d '"' || true)
        fi
    fi
    [[ "$bucket" == "your-gcs-bucket" ]] && bucket=""
    echo "$bucket"
}

# ---------------------------------------------------------------------------
# Try to delete all objects from a real GCS bucket
# Tries: gsutil → gcloud → python3 (installs google-cloud-storage if needed)
# ---------------------------------------------------------------------------
delete_gcs_objects() {
    local bucket="$1"
    local sa_key_path="${GCP_SA_KEY_PATH:-}"
    local sa_key_json="${GCP_SA_KEY_JSON:-}"

    # Write SA key to temp file if provided as JSON string
    local tmp_key=""
    if [[ -z "$sa_key_path" && -n "$sa_key_json" ]]; then
        tmp_key=$(mktemp /tmp/gcp-sa-key-XXXXXX.json)
        echo "$sa_key_json" > "$tmp_key"
        sa_key_path="$tmp_key"
    fi

    local deleted=0

    if command -v gsutil &>/dev/null; then
        info "Using gsutil..."
        GOOGLE_APPLICATION_CREDENTIALS="${sa_key_path:-}" \
            gsutil -m rm -r "gs://$bucket/**" 2>/dev/null && deleted=1 || true

    elif command -v gcloud &>/dev/null; then
        info "Using gcloud storage..."
        GOOGLE_APPLICATION_CREDENTIALS="${sa_key_path:-}" \
            gcloud storage rm --recursive "gs://$bucket/**" 2>/dev/null && deleted=1 || true
    fi

    if [[ "$deleted" -eq 0 ]]; then
        # Try python3 + google-cloud-storage (install if needed)
        if python3 -c "from google.cloud import storage" 2>/dev/null || \
           pip3 install --quiet google-cloud-storage 2>/dev/null; then
            info "Using python3 + google-cloud-storage..."
            python3 - <<PYEOF
import os, sys
os.environ.pop("STORAGE_EMULATOR_HOST", None)  # ensure real GCS, not fake-gcs
key = "${sa_key_path}"
try:
    from google.cloud import storage
    client = storage.Client.from_service_account_json(key) if key else storage.Client()
    bucket = client.bucket("${bucket}")
    blobs = list(bucket.list_blobs())
    if blobs:
        bucket.delete_blobs(blobs)
    print(f"Deleted {len(blobs)} object(s) from gs://${bucket}")
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
            deleted=$?
        fi
    fi

    [[ -n "$tmp_key" ]] && rm -f "$tmp_key"
    return $((deleted == 0 ? 1 : 0))
}

# ---------------------------------------------------------------------------
# GCS Cleanup
# ---------------------------------------------------------------------------
echo "--- GCS Cleanup -----------------------------------------------"

# Source .env for GCP credentials if available
[[ -f "$ENV_FILE" ]] && source "$ENV_FILE" 2>/dev/null || true

GCS_BUCKET=$(detect_gcs_bucket)

if [[ -n "$GCS_BUCKET" ]]; then
    info "Deleting objects from gs://$GCS_BUCKET ..."
    if delete_gcs_objects "$GCS_BUCKET"; then
        ok "gs://$GCS_BUCKET wiped"
    else
        warn "Could not auto-delete GCS objects."
        echo ""
        echo "  Delete manually via GCS Console:"
        echo "    https://console.cloud.google.com/storage/browser/$GCS_BUCKET"
        echo "    → select all objects → Delete"
        echo ""
        echo "  Or with gcloud CLI:"
        echo "    gcloud storage rm --recursive 'gs://$GCS_BUCKET/**'"
    fi
else
    echo "  No real GCS bucket configured — skipping."
fi

# fake-gcs note (in-memory — wiped automatically with pod deletion)
fake_pod=$(kubectl get pods -n "$NAMESPACE" -l app=fake-gcs-local \
    --no-headers 2>/dev/null | { grep Running || true; } | awk '{print $1}' | head -1 || true)
[[ -n "$fake_pod" ]] && info "fake-gcs (in-memory) will be wiped when pod is deleted."

echo ""

# ---------------------------------------------------------------------------
# Remove Kubernetes resources
# ---------------------------------------------------------------------------
kubectl delete job e2e-tests -n "$NAMESPACE" --ignore-not-found 2>/dev/null && ok "Deleted e2e-tests job" || true
helm uninstall graph-olap   -n "$NAMESPACE" 2>/dev/null && ok "Uninstalled graph-olap"   || warn "graph-olap not installed"
helm uninstall jupyter-labs -n "$NAMESPACE" 2>/dev/null && ok "Uninstalled jupyter-labs" || warn "jupyter-labs not installed"
helm uninstall local-infra  -n "$NAMESPACE" 2>/dev/null && ok "Uninstalled local-infra"  || warn "local-infra not installed"
kubectl delete namespace "$NAMESPACE" --ignore-not-found && ok "Deleted namespace $NAMESPACE"

echo ""
echo -e "${GREEN}Teardown complete.${NC}"
echo ""
echo "To also remove the nginx ingress controller:"
echo "  helm uninstall ingress-nginx -n ingress-nginx"
echo "  kubectl delete namespace ingress-nginx"
