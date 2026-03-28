"""HTTP client with retry logic and error handling."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from graph_olap.exceptions import (
    exception_from_response,
)

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client with retry logic and error handling.

    Features:
    - Automatic retry for transient failures (connection errors, 503)
    - Exponential backoff between retries
    - Automatic error response parsing to SDK exceptions
    - Request/response logging

    Authentication:
    - api_key: Uses 'Authorization: Bearer {key}' header (production)
    - internal_api_key: Uses 'X-Internal-Api-Key: {key}' header (internal)
    - username: Uses 'X-Username: {username}' header (development/testing)

    If both api_key and internal_api_key are provided, internal_api_key takes precedence.
    Username is always sent if provided (required for user-scoped API routes).

    Example:
        >>> client = HTTPClient(
        ...     base_url="https://api.example.com",
        ...     api_key="sk-xxx",
        ...     timeout=30.0,
        ...     max_retries=3,
        ... )
        >>> response = client.get("/api/mappings")
        >>> client.close()
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        internal_api_key: str | None = None,
        username: str | None = None,
        role: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize HTTP client.

        Args:
            base_url: Base URL for API requests
            api_key: API key for authentication (Bearer token)
            internal_api_key: Internal API key (X-Internal-Api-Key header)
            username: Username for user-scoped routes (X-Username header)
            role: User role for X-User-Role header (e.g., "analyst", "admin", "ops")
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for transient failures
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.internal_api_key = internal_api_key
        self.username = username
        self.role = role
        self.timeout = timeout
        self.max_retries = max_retries

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "graph-olap-sdk/0.1.0",
        }
        # Internal API key takes precedence (for internal service calls)
        if internal_api_key:
            headers["X-Internal-Api-Key"] = internal_api_key
        elif api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Username is always sent if provided (required for user-scoped API routes)
        if username:
            headers["X-Username"] = username

        # Role is sent if provided (for development/testing with role-based access)
        if role:
            headers["X-User-Role"] = role

        self._client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout),
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> HTTPClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make GET request.

        Args:
            path: Request path (relative to base_url)
            params: Query parameters

        Returns:
            Response JSON as dict

        Raises:
            GraphOLAPError: On API error
        """
        logger.debug("GET %s params=%s", path, params)
        response = self._client.get(path, params=params)
        return self._handle_response(response)

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def get_text(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Make GET request and return raw text response.

        Used for endpoints that return non-JSON content (e.g., Prometheus metrics).

        Args:
            path: Request path (relative to base_url)
            params: Query parameters

        Returns:
            Response body as text

        Raises:
            GraphOLAPError: On API error
        """
        logger.debug("GET %s params=%s (text response)", path, params)
        response = self._client.get(path, params=params)

        # Check for error status codes
        if response.status_code not in (200, 201, 202, 204):
            # Try to parse as JSON error, fallback to text
            try:
                error_data = response.json()
                error_code = error_data.get("error", {}).get("code")
                message = error_data.get("error", {}).get("message", "Unknown error")
                details = error_data.get("error", {}).get("details", {})
            except Exception:
                error_code = None
                message = response.text or f"HTTP {response.status_code}"
                details = {}

            raise exception_from_response(
                status_code=response.status_code,
                error_code=error_code,
                message=message,
                details=details,
            )

        logger.debug("Response: %d (text, %d bytes)", response.status_code, len(response.content))
        return response.text

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make POST request.

        Args:
            path: Request path (relative to base_url)
            json: Request body as dict

        Returns:
            Response JSON as dict

        Raises:
            GraphOLAPError: On API error
        """
        logger.debug("POST %s json=%s", path, json)
        response = self._client.post(path, json=json)
        return self._handle_response(response)

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def put(
        self,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make PUT request.

        Args:
            path: Request path (relative to base_url)
            json: Request body as dict

        Returns:
            Response JSON as dict

        Raises:
            GraphOLAPError: On API error
        """
        logger.debug("PUT %s json=%s", path, json)
        response = self._client.put(path, json=json)
        return self._handle_response(response)

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def delete(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make DELETE request.

        Args:
            path: Request path (relative to base_url)
            json: Optional JSON body for DELETE request

        Returns:
            Response JSON as dict (usually empty for deletes)

        Raises:
            GraphOLAPError: On API error
        """
        logger.debug("DELETE %s json=%s", path, json)
        response = self._client.request("DELETE", path, json=json)
        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle HTTP response, raising appropriate exceptions.

        Args:
            response: httpx Response object

        Returns:
            Response JSON as dict

        Raises:
            GraphOLAPError: On error responses
        """
        logger.debug("Response: %d", response.status_code)

        # Success responses
        if response.status_code in (200, 201, 202, 204):
            if response.status_code == 204 or not response.content:
                return {}
            return response.json()

        # Error responses
        try:
            error_data = response.json()
            # Support both standard ErrorResponse format and FastAPI default format
            if "error" in error_data:
                # Standard format: {"error": {"code": "...", "message": "...", "details": {}}}
                error_code = error_data.get("error", {}).get("code")
                message = error_data.get("error", {}).get("message", "Unknown error")
                details = error_data.get("error", {}).get("details", {})
            elif "detail" in error_data:
                # FastAPI default format: {"detail": "message"}
                error_code = None
                message = error_data.get("detail", "Unknown error")
                details = {}
            else:
                # Unknown format
                error_code = None
                message = str(error_data)
                details = {}
        except Exception:
            error_code = None
            message = response.text or f"HTTP {response.status_code}"
            details = {}

        raise exception_from_response(
            status_code=response.status_code,
            error_code=error_code,
            message=message,
            details=details,
        )


class AsyncHTTPClient:
    """Async HTTP client with retry logic and error handling.

    Same features as HTTPClient but for async usage:
    - Automatic retry for transient failures
    - Exponential backoff between retries
    - Automatic error response parsing to SDK exceptions

    Authentication:
    - api_key: Uses 'Authorization: Bearer {key}' header (production)
    - internal_api_key: Uses 'X-Internal-Api-Key: {key}' header (internal)
    - username: Uses 'X-Username: {username}' header (development/testing)

    If both api_key and internal_api_key are provided, internal_api_key takes precedence.
    Username is always sent if provided (required for user-scoped API routes).
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        internal_api_key: str | None = None,
        username: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize async HTTP client."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.internal_api_key = internal_api_key
        self.username = username
        self.timeout = timeout
        self.max_retries = max_retries

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "graph-olap-sdk/0.1.0",
        }
        # Internal API key takes precedence (for internal service calls)
        if internal_api_key:
            headers["X-Internal-Api-Key"] = internal_api_key
        elif api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Username is always sent if provided (required for user-scoped API routes)
        if username:
            headers["X-Username"] = username

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout),
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHTTPClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make async GET request."""
        logger.debug("GET %s params=%s", path, params)
        response = await self._client.get(path, params=params)
        return self._handle_response(response)

    async def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make async POST request."""
        logger.debug("POST %s json=%s", path, json)
        response = await self._client.post(path, json=json)
        return self._handle_response(response)

    async def put(
        self,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make async PUT request."""
        logger.debug("PUT %s json=%s", path, json)
        response = await self._client.put(path, json=json)
        return self._handle_response(response)

    async def delete(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make async DELETE request."""
        logger.debug("DELETE %s json=%s", path, json)
        response = await self._client.request("DELETE", path, json=json)
        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle HTTP response (same logic as sync client)."""
        logger.debug("Response: %d", response.status_code)

        if response.status_code in (200, 201, 202, 204):
            if response.status_code == 204 or not response.content:
                return {}
            return response.json()

        try:
            error_data = response.json()
            # Support both standard ErrorResponse format and FastAPI default format
            if "error" in error_data:
                # Standard format: {"error": {"code": "...", "message": "...", "details": {}}}
                error_code = error_data.get("error", {}).get("code")
                message = error_data.get("error", {}).get("message", "Unknown error")
                details = error_data.get("error", {}).get("details", {})
            elif "detail" in error_data:
                # FastAPI default format: {"detail": "message"}
                error_code = None
                message = error_data.get("detail", "Unknown error")
                details = {}
            else:
                # Unknown format
                error_code = None
                message = str(error_data)
                details = {}
        except Exception:
            error_code = None
            message = response.text or f"HTTP {response.status_code}"
            details = {}

        raise exception_from_response(
            status_code=response.status_code,
            error_code=error_code,
            message=message,
            details=details,
        )
