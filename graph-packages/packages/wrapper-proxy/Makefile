# wrapper-proxy - Container Build
SHELL := /bin/bash
IMAGE_NAME ?= wrapper-proxy
TAG ?= latest
REGISTRY ?= europe-west2-docker.pkg.dev/hsbc-graph/hsbc-graph

.PHONY: help build push deploy status logs clean

help:
	@echo "$(IMAGE_NAME) - Graph OLAP Wrapper Proxy"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  make build [TAG=x]       Build Docker image"
	@echo "  make push [TAG=x]        Push to registry"
	@echo "  make deploy              Deploy to cluster"
	@echo "  make status              Check deployment"
	@echo ""
	@echo "Operations:"
	@echo "  make logs                Tail service logs"
	@echo "  make clean               Remove artifacts"

build:
	@echo "Building $(IMAGE_NAME):$(TAG)..."
	docker build -t $(IMAGE_NAME):$(TAG) .

push:
	@echo "Pushing $(IMAGE_NAME):$(TAG)..."
	docker tag $(IMAGE_NAME):$(TAG) $(REGISTRY)/$(IMAGE_NAME):$(TAG)
	docker push $(REGISTRY)/$(IMAGE_NAME):$(TAG)

deploy:
	@echo "Deploy via top-level Makefile or Helm"

status:
	kubectl get pods -n graph-olap-platform -l app=$(IMAGE_NAME)

logs:
	kubectl logs -n graph-olap-platform -l app=$(IMAGE_NAME) -f --tail=100

clean:
	docker rmi $(IMAGE_NAME):$(TAG) 2>/dev/null || true
	docker rmi $(REGISTRY)/$(IMAGE_NAME):$(TAG) 2>/dev/null || true
