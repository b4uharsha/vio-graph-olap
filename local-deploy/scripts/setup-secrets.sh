#!/usr/bin/env bash
# Interactive credential setup for Graph OLAP local deployment.
# Prompts for each value, writes .env, and optionally applies secrets live.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$LOCAL_DEPLOY_DIR/.env"
VALUES_FILE="$LOCAL_DEPLOY_DIR/helm/values-local.yaml"

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()   { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()     { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()   { echo -e "${YELLOW}[WARN]${NC}  $1"; }
prompt() { echo -e "${CYAN}$1${NC}"; }
hint()   { echo -e "\033[0;90m      ↳ $1\033[0m"; }

echo ""
echo "================================================"
echo " Graph OLAP — Credential Setup"
echo "================================================"
echo ""
echo " Sets up credentials for the FULL export pipeline."
echo " Instructions are shown before each question."
echo ""
echo " Press Enter on any question to keep the current value."
echo " Demo notebooks work WITHOUT credentials (fake-GCS, no Starburst)."
echo "================================================"
echo ""

# ---------------------------------------------------------------------------
# Read existing .env values as defaults
# ---------------------------------------------------------------------------
current_monorepo=""
current_starburst_url=""
current_starburst_user=""
current_starburst_password=""
current_gcs_bucket=""
current_gcp_project=""
current_sa_key_path=""

if [[ -f "$ENV_FILE" ]]; then
    source "$ENV_FILE" 2>/dev/null || true
    current_starburst_user="${STARBURST_USER:-}"
    current_starburst_password="${STARBURST_PASSWORD:-}"
    current_sa_key_path="${GCP_SA_KEY_PATH:-}"
fi

# Read current values-local.yaml values
if [[ -f "$VALUES_FILE" ]]; then
    current_starburst_url=$(grep -A1 "starburst:" "$VALUES_FILE" | { grep "url:" || true; } | head -1 | awk '{print $2}' | tr -d '"' || echo "")
    current_gcs_bucket=$({ grep "bucket:" "$VALUES_FILE" || true; } | head -1 | awk '{print $2}' | tr -d '"' || echo "")
    current_gcp_project=$({ grep "gcpProject:" "$VALUES_FILE" || true; } | head -1 | awk '{print $2}' | tr -d '"' || echo "")
fi

# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------
ask() {
    local var_name="$1"
    local label="$2"
    local current="$3"
    local secret="${4:-false}"

    if [[ -n "$current" ]]; then
        if [[ "$secret" == "true" ]]; then
            prompt "  $label [current: ****]: "
        else
            prompt "  $label [current: $current]: "
        fi
    else
        prompt "  $label: "
    fi

    if [[ "$secret" == "true" ]]; then
        read -rs value
        echo ""
    else
        read -r value
    fi

    if [[ -z "$value" && -n "$current" ]]; then
        value="$current"
    fi

    printf -v "$var_name" '%s' "$value"
}

# ---------------------------------------------------------------------------
# Section 1: Starburst Galaxy
# ---------------------------------------------------------------------------
echo "--- Starburst Galaxy ----------------------------------------"
echo ""

hint "Open https://galaxy.starburst.io → Clusters → your cluster"
hint "Click 'Connection info' — copy the hostname (e.g. mycluster.trino.galaxy.starburst.io)"
hint "You can paste the full browser URL too — it will be normalised automatically."
ask starburst_url "Cluster host" "$current_starburst_url"

# Normalise: strip trailing slashes and path segments, add https:// if missing
if [[ -n "$starburst_url" ]]; then
    starburst_url="${starburst_url%%/*}"           # strip any path like /cluster/...
    starburst_url="${starburst_url#https://}"      # remove https:// if present
    starburst_url="${starburst_url#http://}"       # remove http:// if present
    starburst_url="https://${starburst_url}"       # re-add canonical https://
fi

echo ""
hint "Open https://galaxy.starburst.io → Settings → Service Accounts"
hint "Create a service account (or use existing). The email looks like: svc@myorg.galaxy.starburst.io"
ask starburst_user "Service account email" "$current_starburst_user"

echo ""
hint "The password you set when creating the service account above."
ask starburst_pass "Service account password" "$current_starburst_password" true

echo ""

# ---------------------------------------------------------------------------
# Section 2: Google Cloud Storage
# ---------------------------------------------------------------------------
echo "--- Google Cloud Storage ------------------------------------"
echo ""

hint "Open https://console.cloud.google.com"
hint "Your project ID is shown in the top-left dropdown (e.g. my-project-123456)"
hint "It is NOT the project name — it's the ID with hyphens and numbers."
ask gcp_project "GCP project ID" "$current_gcp_project"

echo ""
hint "GCP Console → Cloud Storage → Buckets → pick or create a bucket."
hint "Use a globally unique name (e.g. mycompany-graph-olap-exports)."
ask gcs_bucket "GCS bucket name" "$current_gcs_bucket"

echo ""
hint "GCP Console → IAM & Admin → Service Accounts → select your SA"
hint "→ Keys tab → Add Key → Create new key → JSON → download the file."
hint "Then provide the path to that downloaded JSON file below."
ask sa_key_path "Path to SA key JSON file" "$current_sa_key_path"

# Expand tilde in path
sa_key_path="${sa_key_path/#\~/$HOME}"

echo ""

# ---------------------------------------------------------------------------
# Validate SA key file if provided
# ---------------------------------------------------------------------------
sa_key_json=""
if [[ -n "$sa_key_path" ]]; then
    if [[ ! -f "$sa_key_path" ]]; then
        warn "File not found: $sa_key_path — skipping GCS key"
        sa_key_path=""
    else
        sa_key_json=$(cat "$sa_key_path")
        ok "Service account key loaded ($(wc -c < "$sa_key_path" || echo 0) bytes)"
    fi
fi

# ---------------------------------------------------------------------------
# Write .env
# ---------------------------------------------------------------------------
echo ""
info "Writing $ENV_FILE ..."

cat > "$ENV_FILE" << EOF
# Graph OLAP Local Deployment — generated by 'make secrets'
# Re-run 'make secrets' to update. Source with: source .env

# Starburst Galaxy
$([ -n "$starburst_user" ] && echo "export STARBURST_USER=\"$starburst_user\"" || echo "# export STARBURST_USER=")
$([ -n "$starburst_pass" ] && echo "export STARBURST_PASSWORD=\"$starburst_pass\"" || echo "# export STARBURST_PASSWORD=")

# GCP service account key (JSON content — used to create the K8s secret)
$([ -n "$sa_key_path" ] && echo "export GCP_SA_KEY_PATH=\"$sa_key_path\"" || echo "# export GCP_SA_KEY_PATH=")
$([ -n "$sa_key_json" ] && echo "export GCP_SA_KEY_JSON=\$(cat \"$sa_key_path\")" || echo "# export GCP_SA_KEY_JSON=")
EOF

ok ".env written"

# ---------------------------------------------------------------------------
# Update values-local.yaml placeholders
# ---------------------------------------------------------------------------
info "Updating helm/values-local.yaml ..."

update_yaml_value() {
    local file="$1"
    local key="$2"
    local new_val="$3"
    # Replace first occurrence of "key: anything" with "key: new_val"
    sed -i.bak "s|^\([[:space:]]*${key}:\).*|\1 \"${new_val}\"|" "$file" && rm -f "${file}.bak"
}

[[ -n "$starburst_url" ]]  && update_yaml_value "$VALUES_FILE" "url"        "$starburst_url"
[[ -n "$starburst_user" ]] && update_yaml_value "$VALUES_FILE" "user"       "$starburst_user"
[[ -n "$gcs_bucket" ]]     && update_yaml_value "$VALUES_FILE" "bucket"     "$gcs_bucket"
[[ -n "$gcp_project" ]]    && update_yaml_value "$VALUES_FILE" "gcpProject" "$gcp_project"

# Real GCP SA key provided → disable fake-gcs emulator so wrapper uses real GCS.
# No SA key → keep fake-gcs emulator so local dev works without GCP credentials.
if [[ -n "$sa_key_json" ]]; then
    update_yaml_value "$VALUES_FILE" "storageEmulatorHost" ""
    ok "Real GCS SA key provided — storageEmulatorHost cleared (using real GCS)"
else
    update_yaml_value "$VALUES_FILE" "storageEmulatorHost" "http://fake-gcs-local:4443"
    info "No SA key — storageEmulatorHost kept as fake-gcs-local (local dev mode)"
fi

ok "values-local.yaml updated"

# ---------------------------------------------------------------------------
# Apply secrets to running cluster (if running)
# ---------------------------------------------------------------------------
NAMESPACE="graph-olap-local"
if kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo ""
    prompt "  Cluster namespace '$NAMESPACE' is running. Apply secrets now? [Y/n]: "
    read -r apply_now
    apply_now="${apply_now:-Y}"

    if [[ "$apply_now" =~ ^[Yy]$ ]]; then
        # Starburst secret
        if [[ -n "$starburst_pass" ]]; then
            kubectl create secret generic export-worker-secrets \
                --from-literal=STARBURST_PASSWORD="$starburst_pass" \
                --from-literal=GRAPH_OLAP_INTERNAL_API_KEY="test-internal-api-key" \
                -n "$NAMESPACE" \
                --dry-run=client -o yaml | kubectl apply -f - 2>/dev/null
            ok "Starburst secret applied"
        fi

        # GCS SA key secret
        if [[ -n "$sa_key_json" ]]; then
            kubectl create secret generic gcp-sa-key \
                --from-literal=key.json="$sa_key_json" \
                -n "$NAMESPACE" \
                --dry-run=client -o yaml | kubectl apply -f - 2>/dev/null
            ok "GCP SA key secret applied"
        fi

        echo ""
        info "Restarting services to pick up new credentials..."
        kubectl rollout restart deployment/graph-olap-export-worker -n "$NAMESPACE" 2>/dev/null || true
        ok "export-worker restarting"
        # control-plane also needs restart — it passes GCP_PROJECT to wrapper pods
        kubectl rollout restart deployment/graph-olap-control-plane -n "$NAMESPACE" 2>/dev/null || true
        ok "control-plane restarting (applies GCP project to new wrapper pods)"
    fi
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "================================================"
ok "Credentials configured!"
echo "================================================"
echo ""
echo "  Next steps:"
echo ""
if [[ -n "$starburst_user" && -n "$sa_key_json" ]]; then
    echo "  All credentials configured — ready for full pipeline:"
    echo "  1. make build              — build Docker images (no credentials needed)"
    echo "  2. source .env"
    echo "  3. make deploy             — deploys with your credentials"
else
    echo "  Partial credentials — demo notebooks will work:"
    echo "  1. make build              — build Docker images"
    echo "  2. make deploy             — deploys (demo mode, fake-GCS)"
    echo ""
    [[ -z "$starburst_user" ]] && echo "  Missing: Starburst credentials (export jobs will fail)"
    [[ -z "$sa_key_json" ]]   && echo "  Missing: GCP SA key (real GCS disabled, fake-GCS used)"
fi
echo ""
echo "  • make status                  — check pod health"
echo ""
