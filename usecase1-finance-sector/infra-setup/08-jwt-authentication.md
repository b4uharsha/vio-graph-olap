# JWT Authentication Flow

This guide covers the JWT-based authentication flow for the Graph OLAP platform.

## Overview

The platform supports two authentication modes:

| Mode | Use Case | Headers |
|------|----------|---------|
| **External** | API Gateway / OAuth2 Proxy | `Authorization: Bearer <JWT>` |
| **In-Cluster** | Internal services | `X-Username`, `X-User-Role` |

## 1. JWT Token Structure

### Required Claims

```json
{
  "sub": "auth0|user123",
  "iss": "https://your-tenant.auth0.com/",
  "aud": "https://api.your-domain.com",
  "exp": 1710000000,
  "iat": 1709900000,
  "https://api.your-domain.com/email": "user@example.com",
  "https://api.your-domain.com/roles": ["analyst", "admin"]
}
```

### Claim URLs

Configure custom claim URLs in your identity provider:

| Claim | URL | Purpose |
|-------|-----|---------|
| Email | `https://api.your-domain.com/email` | User identification |
| Roles | `https://api.your-domain.com/roles` | Authorization |

## 2. Control Plane Configuration

```yaml
# config.yaml
env:
  # JWKS endpoint for token validation
  AUTH0_JWKS_URL: "https://your-tenant.auth0.com/.well-known/jwks.json"

  # Expected audience (your API identifier)
  AUTH0_AUDIENCE: "https://api.your-domain.com"

  # Expected issuer
  AUTH0_ISSUER: "https://your-tenant.auth0.com/"

  # Custom claim URLs
  JWT_EMAIL_CLAIM_URL: "https://api.your-domain.com/email"
  JWT_ROLES_CLAIM_URL: "https://api.your-domain.com/roles"
```

## 3. External Authentication Flow (OAuth2 Proxy)

### Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Client    │────▶│  OAuth2 Proxy   │────▶│  Control Plane  │
│             │     │                 │     │                 │
│  Bearer JWT │     │  Validates JWT  │     │  Receives:      │
│             │     │  Extracts email │     │  X-Username     │
│             │     │  Forwards auth  │     │  Authorization  │
└─────────────┘     └─────────────────┘     └─────────────────┘
```

### OAuth2 Proxy Configuration

```yaml
# oauth2-proxy-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oauth2-proxy
  namespace: graph-olap
spec:
  replicas: 2
  selector:
    matchLabels:
      app: oauth2-proxy
  template:
    metadata:
      labels:
        app: oauth2-proxy
    spec:
      containers:
        - name: oauth2-proxy
          image: quay.io/oauth2-proxy/oauth2-proxy:v7.6.0
          args:
            - --upstream=static://202
            - --reverse-proxy=true
            - --provider=oidc
            - --oidc-issuer-url=https://your-tenant.auth0.com/
            - --oidc-jwks-url=https://your-tenant.auth0.com/.well-known/jwks.json
            - --oidc-extra-audience=https://api.your-domain.com
            - --oidc-email-claim=https://api.your-domain.com/email
            - --email-domain=*
            - --skip-jwt-bearer-tokens=false
            - --skip-auth-preflight=true
            - --set-xauthrequest=true
            - --pass-access-token=true
            - --cookie-secure=true

          env:
            - name: OAUTH2_PROXY_COOKIE_SECRET
              valueFrom:
                secretKeyRef:
                  name: oauth2-proxy-secrets
                  key: cookie-secret
            - name: OAUTH2_PROXY_CLIENT_ID
              value: "your-client-id"
            - name: OAUTH2_PROXY_CLIENT_SECRET
              valueFrom:
                secretKeyRef:
                  name: oauth2-proxy-secrets
                  key: client-secret

          ports:
            - containerPort: 4180
```

### Nginx Ingress Annotations

```yaml
# control-plane-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: control-plane-ingress
  namespace: graph-olap
  annotations:
    nginx.ingress.kubernetes.io/auth-url: "http://oauth2-proxy.graph-olap.svc.cluster.local/oauth2/auth"
    nginx.ingress.kubernetes.io/auth-response-headers: "X-Auth-Request-Email"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      auth_request_set $auth_email $upstream_http_x_auth_request_email;
      proxy_set_header X-Username $auth_email;
      proxy_set_header Authorization $http_authorization;
```

## 4. In-Cluster Authentication Flow

For internal services (kubectl exec, test pods), use header-based auth:

### Environment Variable

```bash
export GRAPH_OLAP_IN_CLUSTER_MODE=true
```

### Header Format

```bash
# Direct header authentication
curl -X GET "http://control-plane:8080/api/instances" \
    -H "X-Username: user@example.com" \
    -H "X-User-Role: analyst"
```

### Testing Module

```python
# testing.py - Persona-based testing
PERSONAS = {
    "analyst": {
        "email": "analyst@example.com",
        "role": "analyst",
    },
    "admin": {
        "email": "admin@example.com",
        "role": "admin",
    },
    "viewer": {
        "email": "viewer@example.com",
        "role": "viewer",
    },
}

def get_auth_headers(persona: str) -> dict:
    """Get auth headers for a test persona."""
    if os.environ.get("GRAPH_OLAP_IN_CLUSTER_MODE"):
        # In-cluster mode: use X-Username/X-User-Role headers
        p = PERSONAS.get(persona, PERSONAS["analyst"])
        return {
            "X-Username": p["email"],
            "X-User-Role": p["role"],
        }
    else:
        # External mode: use API key
        return {
            "Authorization": f"Bearer {os.environ['GRAPH_OLAP_API_KEY']}"
        }
```

## 5. Role-Based Access Control

### Roles

| Role | Permissions |
|------|-------------|
| `viewer` | Read instances, read snapshots |
| `analyst` | Create/delete own instances, query |
| `admin` | All operations, manage all users' resources |

### Implementation

```python
# auth.py
from fastapi import Request, HTTPException

def get_current_user(request: Request) -> User:
    """Extract user from request headers or JWT."""

    # Check for in-cluster headers first
    username = request.headers.get("X-Username")
    role = request.headers.get("X-User-Role")

    if username and role:
        return User(email=username, role=role)

    # Fall back to JWT
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth")

    token = auth_header[7:]
    claims = validate_jwt(token)

    return User(
        email=claims.get(settings.jwt_email_claim_url),
        role=claims.get(settings.jwt_roles_claim_url, ["viewer"])[0],
    )
```

## 6. Wrapper Authentication

Wrappers also validate user identity:

```
┌─────────────────┐     ┌─────────────────┐
│  Client (curl)  │────▶│  Wrapper Pod    │
│                 │     │                 │
│  X-Username     │     │  Validates:     │
│  X-User-Role    │     │  - Username     │
│                 │     │  - Role perms   │
└─────────────────┘     └─────────────────┘
```

### Query with Auth

```bash
curl -X POST "http://wrapper-abc123.graph-olap.svc.cluster.local:8000/query" \
    -H "Content-Type: application/json" \
    -H "X-Username: analyst@example.com" \
    -H "X-User-Role: analyst" \
    -d '{"query": "MATCH (n:Person) RETURN n LIMIT 10"}'
```

## 7. Starburst Role-Based Access

For Starburst queries, roles map to database permissions:

```python
# starburst_client.py
def execute_with_role(query: str, role: str) -> Result:
    """Execute query with SET ROLE for authorization."""
    session = get_starburst_session()

    # Set role before executing user query
    session.execute(f"SET ROLE {role}")
    result = session.execute(query)

    return result
```

### Role Header in Requests

```bash
# The X-User-Role header determines Starburst role
curl -X POST "http://control-plane:8080/api/query" \
    -H "X-Username: user@example.com" \
    -H "X-User-Role: data_analyst" \
    -d '{"query": "SELECT * FROM catalog.schema.table"}'
```

## 8. Security Best Practices

### Token Validation

```python
# Always validate:
# 1. Signature (via JWKS)
# 2. Expiration (exp claim)
# 3. Issuer (iss claim)
# 4. Audience (aud claim)

def validate_jwt(token: str) -> dict:
    try:
        jwks_client = jwt.PyJWKClient(settings.auth0_jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.auth0_audience,
            issuer=settings.auth0_issuer,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, f"Invalid token: {e}")
```

### Header Injection Prevention

```python
# Only trust X-Username/X-User-Role from internal sources
def is_internal_request(request: Request) -> bool:
    """Check if request came through internal network."""
    # Trust headers only if request came from cluster-internal IP
    client_ip = request.client.host
    return client_ip.startswith("10.") or client_ip.startswith("172.")
```

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Authentication Flow                               │
└─────────────────────────────────────────────────────────────────────┘

External Request:

  Client ──Bearer JWT──▶ Ingress ──▶ OAuth2 Proxy ──▶ Control Plane
                                          │
                                    Validates JWT
                                    Extracts email
                                    Sets X-Username
                                          │
                                          ▼
                                    Control Plane
                                    reads X-Username
                                    + Authorization
                                    extracts role


In-Cluster Request:

  kubectl exec ──▶ curl with X-Username/X-User-Role ──▶ Control Plane
       │                                                      │
       │                                              Trusts headers
       │                                              (internal IP)
       │                                                      │
       └──────────────────────────────────────────────────────┘
```

## Next Steps

- [09-testing-validation.md](09-testing-validation.md) - Testing and validation procedures
