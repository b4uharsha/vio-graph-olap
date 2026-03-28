"""Zero-config Jupyter notebook integration.

This module provides the simplest way to get started with Graph OLAP
in a Jupyter notebook environment. Configuration is auto-discovered
from environment variables.

Quick Start (2 lines):
    >>> from graph_olap import notebook
    >>> client = notebook.connect()

For E2E Tests (with automatic cleanup):
    >>> from graph_olap import notebook
    >>> from graph_olap.testing import TestPersona
    >>>
    >>> ctx = notebook.test("CrudTest", persona=TestPersona.ANALYST_ALICE)
    >>> mapping = ctx.mapping(node_definitions=[...])
    >>> snapshot = ctx.snapshot(mapping)
    >>> instance = ctx.instance(snapshot)
    >>> conn = ctx.connect(instance)
    >>>
    >>> # Cleanup happens automatically on exit!

Environment Variables:
    GRAPH_OLAP_API_URL: Control plane URL (required)
    GRAPH_OLAP_API_KEY: API key for authentication (optional for connect())

    For testing with typed personas:
    GRAPH_OLAP_API_KEY_ANALYST_ALICE: API key for Alice (analyst)
    GRAPH_OLAP_API_KEY_ANALYST_BOB: API key for Bob (analyst)
    GRAPH_OLAP_API_KEY_ADMIN_CAROL: API key for Carol (admin)
    GRAPH_OLAP_API_KEY_OPS_DAVE: API key for Dave (ops)

The connect() function also:
    - Configures itables for automatic interactive DataFrames
    - Sets up rich HTML display for all result types
    - Provides helpful error messages for common issues
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from graph_olap.client import GraphOLAPClient

if TYPE_CHECKING:
    from graph_olap.testing import NotebookTest, TestPersona

# Global client for notebook convenience
_current_client: GraphOLAPClient | None = None

# Track if styles have been set up
_styles_setup_done: bool = False


def connect(
    api_url: str | None = None,
    api_key: str | None = None,
    **kwargs: Any,
) -> GraphOLAPClient:
    """Connect to Graph OLAP Platform with auto-discovery.

    This is the recommended entry point for Jupyter notebooks.
    Configuration is auto-discovered from environment variables,
    or can be provided explicitly.

    Args:
        api_url: Override GRAPH_OLAP_API_URL environment variable
        api_key: Override GRAPH_OLAP_API_KEY environment variable
        **kwargs: Additional config options (timeout, max_retries)

    Returns:
        Configured GraphOLAPClient ready for use

    Raises:
        ValueError: If GRAPH_OLAP_API_URL is not set

    Example:
        >>> from graph_olap import notebook
        >>> client = notebook.connect()

        >>> # Or with explicit configuration
        >>> client = notebook.connect(
        ...     api_url="https://graph-olap.example.com",
        ...     api_key="sk-xxx",
        ... )

        >>> # Start working immediately
        >>> mappings = client.mappings.list()
    """
    global _current_client

    # Initialize itables for interactive DataFrames if available
    _setup_itables()

    # Create and store client
    _current_client = GraphOLAPClient.from_env(
        api_url=api_url,
        api_key=api_key,
        **kwargs,
    )

    return _current_client


def init(
    api_url: str | None = None,
    api_key: str | None = None,
    **kwargs: Any,
) -> GraphOLAPClient:
    """Alias for connect() - initialize Graph OLAP SDK for notebooks.

    See connect() for full documentation.
    """
    return connect(api_url=api_url, api_key=api_key, **kwargs)


def get_client() -> GraphOLAPClient | None:
    """Get the current notebook client.

    Returns:
        Current GraphOLAPClient or None if not connected
    """
    return _current_client


def _setup_itables() -> None:
    """Configure itables for automatic interactive display."""
    try:
        import itables

        itables.init_notebook_mode(all_interactive=True)
    except ImportError:
        pass  # itables not installed, skip


def _setup_display() -> None:
    """Configure rich display for Jupyter."""
    try:
        from IPython import get_ipython

        ip = get_ipython()
        if ip is not None:
            # Enable HTML display for our models
            pass  # Models already have _repr_html_ methods
    except ImportError:
        pass


def _setup_notebook_styles() -> None:
    """Inject notebook CSS into IPython display.

    Loads CSS from the SDK package resources, ensuring styles are always
    available regardless of the notebook's working directory.

    This function is called automatically on module import and is idempotent.
    """
    global _styles_setup_done
    if _styles_setup_done:
        return
    _styles_setup_done = True

    try:
        from IPython import get_ipython
        from IPython.display import HTML, display

        ip = get_ipython()
        if ip is None:
            return

        # Load CSS from SDK package resources (always available)
        from graph_olap.styles import get_notebook_css

        css = get_notebook_css()
        display(HTML(f"<style>\n{css}\n</style>"))

    except ImportError:
        pass  # IPython not available or styles package missing


def wake_starburst(timeout: int = 60, quiet: bool = False) -> bool:
    """Wake Starburst Galaxy cluster and wait until ready.

    Starburst Galaxy clusters auto-suspend after 5 minutes of inactivity.
    Call this before operations that require Starburst (snapshot creation,
    data export) to ensure the cluster is awake.

    Args:
        timeout: Maximum seconds to wait for cluster to be ready
        quiet: If True, suppress progress messages

    Returns:
        True if cluster is ready, False if wake-up failed or timed out

    Environment Variables:
        STARBURST_USER: Galaxy service account username
        STARBURST_PASSWORD: Galaxy service account password
        STARBURST_TRINO_URL: Trino endpoint (default: your-cluster.trino.galaxy.starburst.io)

    Example:
        >>> from graph_olap import notebook
        >>> notebook.wake_starburst()  # Ensure cluster is awake
        >>> ctx = notebook.test("MyTest", persona=TestPersona.ANALYST_ALICE)
        >>> snapshot = ctx.snapshot(mapping)  # Now this won't timeout
    """
    import os
    import time

    starburst_user = os.environ.get("STARBURST_USER")
    starburst_password = os.environ.get("STARBURST_PASSWORD")
    trino_url = os.environ.get(
        "STARBURST_TRINO_URL",
        "https://your-cluster.trino.galaxy.starburst.io",
    )

    if not starburst_user or not starburst_password:
        if not quiet:
            print("⚠️  Starburst credentials not set, skipping cluster wake-up")
        return False

    try:
        import httpx

        with httpx.Client(
            auth=(starburst_user, starburst_password), timeout=30
        ) as client:
            if not quiet:
                print("🔄 Waking Starburst cluster...")

            # Send query to wake cluster
            response = client.post(
                f"{trino_url}/v1/statement",
                content="SELECT 1",
                headers={"X-Trino-User": starburst_user},
            )

            if response.status_code != 200:
                if not quiet:
                    print(f"⚠️  Wake-up request failed: HTTP {response.status_code}")
                return False

            # Poll until ready
            start = time.time()
            while time.time() - start < timeout:
                info = client.get(f"{trino_url}/v1/info")
                if info.status_code == 200 and not info.json().get("starting", True):
                    if not quiet:
                        print("✅ Starburst cluster is ready")
                    return True
                time.sleep(2)

            if not quiet:
                print(f"⚠️  Cluster still starting after {timeout}s, proceeding anyway")
            return True

    except Exception as e:
        if not quiet:
            print(f"⚠️  Failed to wake cluster: {e}")
        return False


def test(prefix: str, *, persona: TestPersona) -> NotebookTest:
    """Create a test context with automatic cleanup.

    This is the recommended entry point for E2E test notebooks. It provides:
    - Auto-naming: Resources get unique names automatically
    - Auto-tracking: Resources created via ctx.* are tracked
    - Guaranteed cleanup: atexit ensures cleanup even on failure
    - Type-safe personas: Explicit identity for each test

    Args:
        prefix: Test name prefix for resource naming (e.g., "CrudTest")
        persona: Which user is running this test (REQUIRED - no default!)

    Returns:
        NotebookTest context with automatic cleanup

    Raises:
        TypeError: If persona is not provided
        ValueError: If required environment variables are missing

    Example:
        >>> from graph_olap import notebook
        >>> from graph_olap.testing import TestPersona
        >>>
        >>> ctx = notebook.test("CrudTest", persona=TestPersona.ANALYST_ALICE)
        >>>
        >>> # Create resources (auto-named, auto-tracked)
        >>> mapping = ctx.mapping(node_definitions=[...])
        >>> snapshot = ctx.snapshot(mapping)
        >>> instance = ctx.instance(snapshot)
        >>> conn = ctx.connect(instance)
        >>>
        >>> # Cleanup happens automatically on exit!
        >>> # Or call ctx.cleanup() for immediate cleanup

    Note:
        Every test must specify a persona - there is no default user.
        This ensures tests are self-documenting about who is acting.
    """
    # Import here to avoid circular imports
    from graph_olap.testing import NotebookTest

    # Initialize itables for interactive DataFrames if available
    _setup_itables()

    # Inject notebook styling functions (styled_table, callout, etc.)
    _setup_notebook_styles()

    return NotebookTest(prefix, persona=persona)


# =============================================================================
# Module-level initialization
# =============================================================================

# Automatically inject styling functions when this module is imported.
# This allows notebooks to use styled_table(), callout(), etc. immediately
# after `from graph_olap import notebook`, without waiting for test() call.
_setup_notebook_styles()
