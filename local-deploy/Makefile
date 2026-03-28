SHELL := /bin/bash

# Path to the graph-olap monorepo (source code + Helm charts).
# Override if your monorepo is in a different location:
#   make deploy MONOREPO_ROOT=/path/to/graph-olap
MONOREPO_ROOT ?= ../graph-olap

# Kubernetes namespace
NAMESPACE ?= graph-olap-local

# Single service to build/deploy (omit for all)
SVC ?=

.PHONY: help prereqs secrets build build-e2e build-status deploy status logs test test-e2e teardown clean-instances clean-old-instances dashboard dashboard-token dashboard-stop

help:
	@echo "Graph OLAP - Local Deployment"
	@echo ""
	@echo "  make prereqs               Check required tools"
	@echo "  make secrets               Configure Starburst + GCS credentials interactively"
	@echo "  make build [SVC=name]      Build Docker images"
	@echo "  make build-e2e             Build the e2e-tests image only"
	@echo "  make build-status          Show which images are built and their sizes"
	@echo "  make deploy                Deploy full stack to local Kubernetes"
	@echo "  make status                Show pod/service status"
	@echo "  make logs SVC=name         Tail logs for a service"
	@echo "  make test                  Run e2e tests locally (pytest on host)"
	@echo "  make test-e2e              Run e2e tests as a Kubernetes Job (in-cluster)"
	@echo "  make clean-instances        Delete all running graph instances + wrapper pods"
	@echo "  make clean-old-instances    Delete instances older than HOURS (default: 2)"
	@echo "  make teardown              Delete namespace and all resources"
	@echo ""
	@echo "  make dashboard             Install + open Kubernetes Dashboard in browser"
	@echo "  make dashboard-token       Print a fresh login token"
	@echo "  make dashboard-stop        Stop the kubectl proxy"
	@echo ""
	@echo "  MONOREPO_ROOT=$(MONOREPO_ROOT)"
	@echo "  NAMESPACE=$(NAMESPACE)"
	@echo ""
	@echo "Services: control-plane export-worker falkordb-wrapper ryugraph-wrapper documentation local-docs jupyter-labs e2e-tests"

prereqs:
	@./scripts/prereqs.sh

secrets:
	@./scripts/setup-secrets.sh

build: prereqs
	@MONOREPO_ROOT="$(MONOREPO_ROOT)" SVC="$(SVC)" ./scripts/build.sh

build-e2e: prereqs
	@MONOREPO_ROOT="$(MONOREPO_ROOT)" SVC="e2e-tests" ./scripts/build.sh

build-status:
	@printf "%-20s %-25s %-10s\n" "IMAGE" "BUILT" "SIZE"
	@printf "%-20s %-25s %-10s\n" "-----" "-----" "----"
	@for svc in control-plane export-worker falkordb-wrapper ryugraph-wrapper documentation local-docs jupyter-labs e2e-tests; do \
		info=$$(docker inspect $$svc:latest --format '{{.Created}} {{.Size}}' 2>/dev/null); \
		if [ -z "$$info" ]; then \
			printf "%-20s %-25s %-10s\n" "$$svc" "—" "not built"; \
		else \
			created=$$(echo $$info | awk '{print $$1}' | xargs -I{} date -j -f "%Y-%m-%dT%H:%M:%S" "{}" "+%Y-%m-%d %H:%M" 2>/dev/null || echo "$$created"); \
			bytes=$$(echo $$info | awk '{print $$2}'); \
			mb=$$(echo "scale=0; $$bytes/1048576" | bc)MB; \
			printf "%-20s %-25s %-10s\n" "$$svc" "$$created" "$$mb"; \
		fi; \
	done

deploy: prereqs
	@MONOREPO_ROOT="$(MONOREPO_ROOT)" NAMESPACE="$(NAMESPACE)" ./scripts/deploy.sh

status:
	@echo "=== Pods ==="
	@kubectl get pods -n $(NAMESPACE) 2>/dev/null || echo "Namespace $(NAMESPACE) not found"
	@echo ""
	@echo "=== Services ==="
	@kubectl get svc -n $(NAMESPACE) 2>/dev/null || true
	@echo ""
	@echo "=== API Health ==="
	@curl -sf http://localhost:30081/health && echo " OK" || echo " not reachable (may still be starting)"

logs:
ifndef SVC
	@echo "Usage: make logs SVC=<service>"
	@echo "Services: control-plane export-worker"
else
	kubectl logs -n $(NAMESPACE) -l app=$(SVC) -f --tail=100
endif

test:
	@cd "$(MONOREPO_ROOT)/tests/e2e" && \
	  ./scripts/run-tests.sh --cluster=orbstack

test-e2e: build-e2e
	@echo "=== Deploying e2e-tests Job ==="
	@kubectl delete job e2e-tests -n $(NAMESPACE) --ignore-not-found
	@kubectl apply -f "$(MONOREPO_ROOT)/tests/e2e/k8s/e2e-test-job.yaml" -n $(NAMESPACE)
	@echo "=== Waiting for Job to complete (timeout 10m) ==="
	@kubectl wait --for=condition=complete job/e2e-tests -n $(NAMESPACE) --timeout=600s || \
	  (kubectl logs job/e2e-tests -n $(NAMESPACE) --tail=50; exit 1)
	@echo "=== Test Logs ==="
	@kubectl logs job/e2e-tests -n $(NAMESPACE)

clean-instances:
	@echo "=== Deleting all running graph instances ==="
	@ids=$$(curl -sf http://localhost:30081/api/instances \
	  -H "X-Username: demo@example.com" -H "X-User-Role: admin" \
	  | python3 -c "import sys,json; data=json.load(sys.stdin); [print(i['id']) for i in data.get('data',[]) if i['status'] in ('running','starting','waiting_for_snapshot')]" 2>/dev/null); \
	if [ -z "$$ids" ]; then \
	  echo "No active instances found"; \
	else \
	  for id in $$ids; do \
	    curl -sf -X DELETE http://localhost:30081/api/instances/$$id \
	      -H "X-Username: demo@example.com" -H "X-User-Role: admin" >/dev/null && echo "  Deleted instance $$id" || echo "  Failed to delete $$id"; \
	  done; \
	fi
	@echo "Done — wrapper pods will terminate shortly"

HOURS ?= 2

define _CLEAN_OLD_PY
import sys, json, datetime, requests, os
api = 'http://localhost:30081'
h   = {'X-Username': 'demo@example.com', 'X-User-Role': 'admin'}
now = datetime.datetime.now(datetime.timezone.utc)
active = {'running','starting','waiting_for_snapshot'}
hours = float(os.environ.get('HOURS', '2'))
data = requests.get(f'{api}/api/instances', headers=h).json().get('data', [])
old  = [i for i in data if i.get('status') in active and i.get('created_at') and
        (now - datetime.datetime.fromisoformat(i['created_at'].replace('Z','+00:00'))).total_seconds() / 3600 >= hours]
if not old:
    print(f'No instances older than {hours}h found.')
    sys.exit(0)
for i in old:
    r = requests.delete(f"{api}/api/instances/{i['id']}", headers=h)
    print(f"  Deleted {i['id']} (status={i['status']})") if r.ok else print(f"  Failed {i['id']}: {r.status_code}")
print(f'Done - deleted {len(old)} instance(s).')
endef
export _CLEAN_OLD_PY

clean-old-instances:
	@echo "=== Deleting instances older than $(HOURS) hour(s) ==="
	@HOURS=$(HOURS) python3 -c "$$_CLEAN_OLD_PY"

teardown:
	@./scripts/teardown.sh $(NAMESPACE)

# ---------------------------------------------------------------------------
# Kubernetes Dashboard
# ---------------------------------------------------------------------------

dashboard:
	@echo "Installing Kubernetes Dashboard..."
	@kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml 2>/dev/null || true
	@kubectl create serviceaccount admin-user -n kubernetes-dashboard 2>/dev/null || true
	@kubectl create clusterrolebinding admin-user \
	  --clusterrole=cluster-admin \
	  --serviceaccount=kubernetes-dashboard:admin-user 2>/dev/null || true
	@kubectl rollout status deployment/kubernetes-dashboard -n kubernetes-dashboard --timeout=60s
	@echo ""
	@echo "=== Login Token (valid 1h) ==="
	@kubectl create token admin-user -n kubernetes-dashboard
	@echo ""
	@echo "=== Starting proxy (http://localhost:8001) ==="
	@pkill -f "kubectl proxy --port=8001" 2>/dev/null || true
	@kubectl proxy --port=8001 &
	@sleep 1
	@echo ""
	@echo "Open: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"
	@echo "Select 'Token' and paste the token printed above."
	@echo "Then switch namespace to '$(NAMESPACE)' in the left sidebar."

dashboard-token:
	@kubectl create token admin-user -n kubernetes-dashboard

dashboard-stop:
	@pkill -f "kubectl proxy --port=8001" 2>/dev/null && echo "Proxy stopped" || echo "No proxy running"
