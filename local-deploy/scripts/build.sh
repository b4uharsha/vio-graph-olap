#!/usr/bin/env bash
# Build all Graph OLAP service images using plain docker build.
# No Earthly or private registries required.
#
# Usage:
#   MONOREPO_ROOT=../../graph-olap ./build.sh                    # Build all services
#   MONOREPO_ROOT=../../graph-olap SVC=control-plane ./build.sh  # Build one service

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
# Default: sibling directory (both repos under the same parent folder)
if [[ -z "${MONOREPO_ROOT:-}" ]] || [[ ! -d "${MONOREPO_ROOT:-}" ]]; then
    MONOREPO_ROOT="$LOCAL_DEPLOY_DIR/../graph-olap"
fi
MONOREPO_ROOT="$(cd "$MONOREPO_ROOT" && pwd)"
DOCKERFILE_DIR="$LOCAL_DEPLOY_DIR/docker"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[BUILD]${NC} $1"; }
ok()      { echo -e "${GREEN}[OK]${NC}    $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# All services (bash 3 compatible — no associative arrays)
ALL_SERVICES="control-plane export-worker falkordb-wrapper ryugraph-wrapper documentation local-docs jupyter-labs e2e-tests"

# Map service name → Dockerfile (bash 3 compatible case statement)
get_dockerfile() {
    case "$1" in
        control-plane)     echo "control-plane.Dockerfile" ;;
        export-worker)     echo "export-worker.Dockerfile" ;;
        falkordb-wrapper)  echo "falkordb-wrapper.Dockerfile" ;;
        ryugraph-wrapper)  echo "ryugraph-wrapper.Dockerfile" ;;
        documentation)     echo "documentation.Dockerfile" ;;
        local-docs)        echo "local-docs.Dockerfile" ;;
        jupyter-labs)      echo "jupyter-labs.Dockerfile" ;;
        e2e-tests)         echo "e2e-tests.Dockerfile" ;;
        *) echo "" ;;
    esac
}

# Detect Kubernetes provider to determine if images need explicit loading.
# Minikube and kind use isolated container runtimes and require explicit image loading.
# OrbStack/Rancher Desktop/Docker Desktop share their own Docker daemon with K8s —
# but only when the BUILD also uses that same daemon. If the active Docker context
# differs from the K8s provider's daemon, images must be piped across.
detect_k8s_provider() {
    local ctx
    ctx=$(kubectl config current-context 2>/dev/null || echo "")
    case "$ctx" in
        orbstack)       echo "orbstack" ;;
        rancher-desktop|docker-desktop) echo "shared" ;;
        minikube)       echo "minikube" ;;
        kind-*|kind)    echo "kind" ;;
        *)              echo "shared" ;;
    esac
}

# Returns the socket path of the active Docker daemon (respects DOCKER_HOST and context).
active_docker_socket() {
    if [[ -n "${DOCKER_HOST:-}" ]]; then
        echo "${DOCKER_HOST#unix://}"
        return
    fi
    local ctx
    ctx=$(docker context show 2>/dev/null || echo "default")
    case "$ctx" in
        orbstack)        echo "$HOME/.orbstack/run/docker.sock" ;;
        rancher-desktop) echo "$HOME/.rd/docker.sock" ;;
        desktop-linux)   echo "$HOME/.docker/run/docker.sock" ;;
        *)               echo "/var/run/docker.sock" ;;
    esac
}

load_image_if_needed() {
    local image="$1"
    local provider
    provider=$(detect_k8s_provider)

    case "$provider" in
        minikube)
            info "Loading $image into minikube..."
            minikube image load "$image"
            ;;
        kind)
            local cluster
            cluster=$(kubectl config current-context 2>/dev/null | sed 's/^kind-//' || echo "unknown")
            info "Loading $image into kind cluster '$cluster'..."
            kind load docker-image "$image" --name "$cluster"
            ;;
        orbstack)
            # OrbStack K8s uses OrbStack's own containerd — images must be in its daemon.
            # If the build used a different daemon (e.g. Docker Desktop), pipe across.
            local orbstack_sock="$HOME/.orbstack/run/docker.sock"
            local active_sock
            active_sock=$(active_docker_socket)
            if [[ "$active_sock" != "$orbstack_sock" ]]; then
                info "Piping $image from build daemon → OrbStack daemon..."
                docker save "$image" | docker -H "unix://$orbstack_sock" load || return 1
            fi
            ;;
        shared)
            ;;  # Rancher Desktop / Docker Desktop: images are immediately available
    esac
}

build_service() {
    local svc="$1"
    local dockerfile
    dockerfile=$(get_dockerfile "$svc")
    local image="${svc}:latest"

    if [[ -z "$dockerfile" ]]; then
        error "Unknown service: $svc"
        error "Valid services: $ALL_SERVICES"
        return 1
    fi

    if [[ ! -f "$DOCKERFILE_DIR/$dockerfile" ]]; then
        error "Dockerfile not found: $DOCKERFILE_DIR/$dockerfile"
        return 1
    fi

    info "$svc → $image"

    # local-docs uses local-deploy/ as its build context (self-contained, no monorepo needed)
    local build_context="$MONOREPO_ROOT"
    if [[ "$svc" == "local-docs" ]]; then
        build_context="$LOCAL_DEPLOY_DIR"
    fi

    # Explicit || return 1: bash disables set -e inside functions called from an
    # "if" condition, so a failing docker build would otherwise be silently ignored.
    docker build \
        --file "$DOCKERFILE_DIR/$dockerfile" \
        --tag "$image" \
        "$build_context" || return 1

    # Also tag wrapper images as :local — the control-plane rejects :latest tags
    # when spawning graph instance pods (safety check for reproducibility).
    case "$svc" in
        ryugraph-wrapper|falkordb-wrapper)
            docker tag "$image" "${svc}:local" || return 1
            load_image_if_needed "${svc}:local" || return 1
            ;;
    esac

    load_image_if_needed "$image" || return 1
    ok "$svc built and ready"
}

main() {
    echo "================================================"
    echo " Graph OLAP Local Build"
    echo "================================================"
    echo " Monorepo: $MONOREPO_ROOT"
    echo ""

    local services_to_build
    if [[ -n "${SVC:-}" ]]; then
        if [[ -z "$(get_dockerfile "$SVC")" ]]; then
            error "Unknown service: $SVC"
            error "Valid services: $ALL_SERVICES"
            exit 1
        fi
        services_to_build="$SVC"
    else
        services_to_build="$ALL_SERVICES"
    fi

    local built=0 failed=0

    for svc in $services_to_build; do
        if build_service "$svc"; then
            built=$((built + 1))
        else
            error "Failed to build $svc"
            failed=$((failed + 1))
        fi
        echo ""
    done

    echo "================================================"
    echo " Built: $built  |  Failed: $failed"
    echo "================================================"

    [ "$failed" -eq 0 ] || exit 1
}

main
