"""Default identity for SDK requests.

The SDK sends X-Username on every request. This module provides the
default username used when no explicit username is passed to the client.

Override at runtime:
    import graph_olap.identity
    graph_olap.identity.DEFAULT_USERNAME = "alice@example.com"

Override via environment:
    export GRAPH_OLAP_USERNAME="ops_dave@e2e.local"
"""

DEFAULT_USERNAME = "analyst_alice@e2e.local"
