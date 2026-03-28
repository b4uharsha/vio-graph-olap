# Appendix A: Environment Variables

This appendix provides a complete reference for all environment variables used by the Graph OLAP SDK.

## Overview

The SDK uses environment variables for configuration, enabling deployment flexibility across development, staging, and production environments. Variables can be set in shell profiles, `.env` files, Kubernetes ConfigMaps, or container orchestration systems.

## Environment Variable Reference

### Core Configuration

| Variable | Required | Description | Default | Example |
|----------|----------|-------------|---------|---------|
| `GRAPH_OLAP_API_URL` | **Yes** | Base URL for the Control Plane API | - | `https://graph-olap.example.com` |
| `GRAPH_OLAP_API_KEY` | **Yes*** | API key for Bearer token authentication | - | `sk-xxx...` |
| `GRAPH_OLAP_INTERNAL_API_KEY` | No | Internal API key for service-to-service calls | - | `internal-key-xxx` |
| `GRAPH_OLAP_USERNAME` | No | Username header for development/testing | - | `analyst@example.com` |

*Required in production environments. Not required if using `GRAPH_OLAP_INTERNAL_API_KEY` or gateway authentication.

### Kubernetes / In-Cluster Configuration

| Variable | Required | Description | Default | Example |
|----------|----------|-------------|---------|---------|
| `GRAPH_OLAP_IN_CLUSTER_MODE` | No | Enable Kubernetes service DNS resolution | `false` | `true` |
| `GRAPH_OLAP_NAMESPACE` | No | Kubernetes namespace for service DNS | `graph-olap-local` | `graph-olap` |

### SDK Behavior Configuration

| Variable | Required | Description | Default | Example |
|----------|----------|-------------|---------|---------|
| `GRAPH_OLAP_TIMEOUT` | No | Default request timeout in seconds | `30.0` | `60.0` |
| `GRAPH_OLAP_MAX_RETRIES` | No | Maximum retry attempts for transient failures | `3` | `5` |

## Detailed Variable Descriptions

### GRAPH_OLAP_API_URL

The base URL for connecting to the Graph OLAP Control Plane API.

**Format:** Full URL including protocol (http/https)

**Examples:**
```bash
# Local development
export GRAPH_OLAP_API_URL="http://localhost:8000"

# Kubernetes cluster (external access)
export GRAPH_OLAP_API_URL="https://graph-olap.example.com"

# Kubernetes cluster (in-cluster service DNS)
export GRAPH_OLAP_API_URL="http://control-plane.graph-olap-local.svc.cluster.local:8000"
```

### GRAPH_OLAP_API_KEY

API key for authentication using the standard Bearer token scheme.

**Format:** String, typically prefixed with `sk-`

**Authentication Header:** `Authorization: Bearer {api_key}`

**Security Notes:**
- Never commit API keys to version control
- Use secrets management in production (Vault, K8s Secrets, etc.)
- Rotate keys periodically

**Example:**
```bash
export GRAPH_OLAP_API_KEY="sk-your-api-key-here"
```

### GRAPH_OLAP_INTERNAL_API_KEY

Internal API key for service-to-service communication within trusted networks.

**Format:** String

**Authentication Header:** `X-Internal-Api-Key: {internal_api_key}`

**Priority:** Takes precedence over `GRAPH_OLAP_API_KEY` when both are set.

**Use Cases:**
- Internal microservice communication
- Background job workers
- E2E testing infrastructure

**Example:**
```bash
export GRAPH_OLAP_INTERNAL_API_KEY="internal-service-key"
```

### GRAPH_OLAP_USERNAME

Username for development and testing environments.

**Format:** String (typically email or identifier)

**Authentication Header:** `X-Username: {username}`

**Important Production Warning:**
In production environments with authentication gateways (e.g., GKE IAP/OIDC):
- This header is **stripped and replaced** by the gateway
- The gateway injects validated identity from the authentication layer
- This variable is **only effective** in local development and E2E testing

**Example:**
```bash
export GRAPH_OLAP_USERNAME="test-user@example.com"
```

### GRAPH_OLAP_IN_CLUSTER_MODE

Enables Kubernetes service DNS resolution for instance connections.

**Format:** `true` or `false` (case-insensitive)

**Behavior when enabled:**
- Instance connections use Kubernetes service DNS names
- Format: `{instance-name}.{namespace}.svc.cluster.local`
- Bypasses external load balancers for direct pod communication

**When to enable:**
- Running in Kubernetes pods (JupyterHub, Jobs)
- E2E tests running inside the cluster
- Any workload that should use internal networking

**Example:**
```bash
export GRAPH_OLAP_IN_CLUSTER_MODE="true"
```

### GRAPH_OLAP_NAMESPACE

Kubernetes namespace for service DNS resolution.

**Format:** Valid Kubernetes namespace name

**Used when:** `GRAPH_OLAP_IN_CLUSTER_MODE` is enabled

**Service DNS Pattern:**
```
{service-name}.{GRAPH_OLAP_NAMESPACE}.svc.cluster.local
```

**Example:**
```bash
export GRAPH_OLAP_NAMESPACE="graph-olap-local"
# Results in DNS: control-plane.graph-olap-local.svc.cluster.local
```

## Configuration Precedence

The SDK follows this precedence order (highest to lowest):

1. **Explicit constructor arguments** - Direct parameters to `GraphOLAPClient()`
2. **`from_env()` parameter overrides** - Arguments passed to `GraphOLAPClient.from_env()`
3. **Environment variables** - Values from the shell environment
4. **Default values** - Built-in SDK defaults

**Example:**
```python
# Environment: GRAPH_OLAP_API_URL="https://prod.example.com"

# Constructor takes precedence
client = GraphOLAPClient(api_url="https://staging.example.com")
# Uses: https://staging.example.com

# from_env() override takes precedence over environment
client = GraphOLAPClient.from_env(api_url="https://dev.example.com")
# Uses: https://dev.example.com

# No override - uses environment variable
client = GraphOLAPClient.from_env()
# Uses: https://prod.example.com
```

## Environment-Specific Configurations

### Local Development

```bash
# .env.local
GRAPH_OLAP_API_URL="http://localhost:8000"
GRAPH_OLAP_USERNAME="developer@example.com"
GRAPH_OLAP_IN_CLUSTER_MODE="false"
```

### K3d / Local Kubernetes

```bash
# .env.k3d
GRAPH_OLAP_API_URL="http://localhost:8000"
GRAPH_OLAP_IN_CLUSTER_MODE="false"
GRAPH_OLAP_NAMESPACE="graph-olap-local"
```

### E2E Testing (In-Cluster)

```bash
# Injected via Kubernetes Job spec
GRAPH_OLAP_API_URL="http://control-plane.graph-olap-local.svc.cluster.local:8000"
GRAPH_OLAP_IN_CLUSTER_MODE="true"
GRAPH_OLAP_NAMESPACE="graph-olap-local"
GRAPH_OLAP_INTERNAL_API_KEY="${INTERNAL_API_KEY}"
```

### Production (GKE with IAP)

```bash
# Injected via Kubernetes ConfigMap/Secrets
GRAPH_OLAP_API_URL="https://graph-olap.prod.example.com"
GRAPH_OLAP_API_KEY="${VAULT_API_KEY}"
GRAPH_OLAP_IN_CLUSTER_MODE="true"
GRAPH_OLAP_NAMESPACE="graph-olap-local"
```

## JupyterHub Configuration

When deploying JupyterHub with the SDK, configure environment variables in the Helm values:

```yaml
# values.yaml
singleuser:
  extraEnv:
    GRAPH_OLAP_API_URL: "http://control-plane.graph-olap-local.svc.cluster.local:8000"
    GRAPH_OLAP_IN_CLUSTER_MODE: "true"
    GRAPH_OLAP_NAMESPACE: "graph-olap-local"
  # API key should come from secrets
  extraEnvFrom:
    - secretRef:
        name: graph-olap-credentials
```

## Validation and Troubleshooting

### Verify Configuration

```python
import os

# Check required variables
required = ["GRAPH_OLAP_API_URL"]
for var in required:
    value = os.environ.get(var)
    if value:
        print(f"{var}: {value[:20]}...")  # Truncate for security
    else:
        print(f"{var}: NOT SET (required)")

# Check optional variables
optional = [
    "GRAPH_OLAP_API_KEY",
    "GRAPH_OLAP_INTERNAL_API_KEY",
    "GRAPH_OLAP_USERNAME",
    "GRAPH_OLAP_IN_CLUSTER_MODE",
    "GRAPH_OLAP_NAMESPACE"
]
for var in optional:
    value = os.environ.get(var)
    if value:
        # Mask sensitive values
        if "KEY" in var:
            print(f"{var}: ***masked***")
        else:
            print(f"{var}: {value}")
    else:
        print(f"{var}: not set")
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ValueError: GRAPH_OLAP_API_URL not set` | Missing required variable | Set `GRAPH_OLAP_API_URL` in environment |
| `AuthenticationError: 401` | Missing or invalid API key | Verify `GRAPH_OLAP_API_KEY` is correct |
| `Connection refused` | Wrong URL or service not running | Check `GRAPH_OLAP_API_URL` and service status |
| `DNS resolution failed` | In-cluster mode misconfigured | Verify namespace and `IN_CLUSTER_MODE` settings |
| `ForbiddenError: 403` | Insufficient permissions | Check user role and API key permissions |

## See Also

- [SDK Quick Start](../01-quick-start.manual.md) - Getting started guide
- [Authentication Guide](../04-authentication.manual.md) - Authentication methods
- [Appendix B: Error Codes](./b-error-codes.manual.md) - Error handling reference
