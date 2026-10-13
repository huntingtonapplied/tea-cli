"""Tea API client — thin wrapper around httpx.

Talks to the Tea FastAPI backend (all routes under /v1). Authenticates with a
developer API key sent in the ``X-API-Key`` header.
"""

import os
import time
from typing import Any, Dict, Optional

import httpx

from tea_cli.config import get_api_key, get_api_url, load_config
from tea_cli.log import logger

# Retry configuration
MAX_RETRIES = int(os.getenv("TEA_MAX_RETRIES", "3"))
RETRY_BACKOFF_BASE = 1.0  # seconds
RETRY_BACKOFF_MAX = 30.0  # seconds
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
RETRYABLE_EXCEPTIONS = (httpx.ConnectError, httpx.TimeoutException)


_ERROR_HINTS = {
    401: [
        "Run: tea login",
        "Or set TEA_API_KEY env var",
    ],
    403: [
        "You may not have access to this resource.",
        "Your API key's scopes may not permit this action.",
    ],
    404: [
        "The resource was not found. Check the ID or URL.",
    ],
    422: [
        "The request data is invalid. Check required fields.",
        "Run: tea <command> --help   for usage details",
    ],
    429: [
        "Rate limit exceeded. Wait a moment and try again.",
    ],
    500: [
        "Server error. Try again in a few minutes.",
    ],
}


def format_error_hint(status_code: int, detail: Optional[str] = None) -> str:
    """Get actionable hint text for an error status code."""
    hints = _ERROR_HINTS.get(status_code, [])
    if not hints:
        return ""
    return "\n".join(f"  {h}" for h in hints)


class TeaClient:
    """HTTP client for the Tea API."""

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None,
                 require_auth: bool = True):
        self.api_key = api_key or get_api_key()
        self.api_url = api_url or get_api_url()

        if require_auth and not self.api_key:
            raise AuthError(
                "Not authenticated.\n"
                "  Run: tea login\n"
                "  Or set TEA_API_KEY env var"
            )

        config = load_config()
        self._timeout = float(os.getenv("TEA_TIMEOUT", config.get("timeout", 60)))
        self._client = httpx.Client(base_url=self.api_url, timeout=self._timeout)
        logger.debug("API client initialized: %s (timeout=%.0fs)", self.api_url, self._timeout)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _request_with_retry(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Execute an HTTP request with retry logic for transient failures."""
        last_exc = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = getattr(self._client, method)(path, headers=self._headers(), **kwargs)
                if resp.status_code not in RETRYABLE_STATUS_CODES or attempt == MAX_RETRIES:
                    return resp
                retry_after = 0.0
                try:
                    retry_after = float(resp.headers.get("Retry-After", 0))
                except (ValueError, TypeError):
                    pass
                delay = min(max(retry_after, RETRY_BACKOFF_BASE * (2 ** attempt)), RETRY_BACKOFF_MAX)
                logger.info(
                    "Retrying %s %s (status %d, attempt %d/%d, waiting %.1fs)",
                    method.upper(), path, resp.status_code, attempt + 1, MAX_RETRIES, delay,
                )
                time.sleep(delay)
            except RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                if attempt == MAX_RETRIES:
                    if isinstance(exc, httpx.ConnectError):
                        raise APIError(
                            f"Cannot connect to {self.api_url}\n"
                            "  Check your network connection\n"
                            "  Verify the API URL: tea doctor",
                            status_code=0,
                        ) from exc
                    if isinstance(exc, httpx.TimeoutException):
                        raise APIError(
                            f"Request timed out after {self._timeout:.0f}s\n"
                            "  Try: TEA_TIMEOUT=120 tea <command>",
                            status_code=0,
                        ) from exc
                    raise
                delay = min(RETRY_BACKOFF_BASE * (2 ** attempt), RETRY_BACKOFF_MAX)
                logger.info(
                    "Retrying %s %s (%s, attempt %d/%d, waiting %.1fs)",
                    method.upper(), path, exc.__class__.__name__, attempt + 1, MAX_RETRIES, delay,
                )
                time.sleep(delay)
        raise last_exc or APIError(f"Request failed after {MAX_RETRIES} retries")

    def get(self, path: str, params: Optional[Dict] = None) -> Any:
        logger.debug("GET %s params=%s", path, params)
        return self._handle_response(self._request_with_retry("get", path, params=params))

    def post(self, path: str, data: Optional[Dict] = None) -> Any:
        logger.debug("POST %s", path)
        return self._handle_response(self._request_with_retry("post", path, json=data))

    def patch(self, path: str, data: Optional[Dict] = None) -> Any:
        logger.debug("PATCH %s", path)
        return self._handle_response(self._request_with_retry("patch", path, json=data))

    def delete(self, path: str) -> Any:
        logger.debug("DELETE %s", path)
        resp = self._request_with_retry("delete", path)
        if resp.status_code == 204:
            return None
        return self._handle_response(resp)

    def _handle_response(self, resp: httpx.Response) -> Any:
        logger.debug("Response %d (%s)", resp.status_code, resp.request.url)
        if resp.status_code == 401:
            raise AuthError(
                "Not authenticated.\n"
                "  Run: tea login\n"
                "  Or set TEA_API_KEY env var"
            )
        if resp.status_code >= 400:
            detail = ""
            try:
                body = resp.json()
                detail = body.get("detail") or body.get("error") or ""
                if isinstance(detail, (dict, list)):
                    detail = str(detail)
                if not detail:
                    detail = resp.text
            except Exception:
                detail = resp.text

            hint = format_error_hint(resp.status_code, detail=detail)
            msg = f"API error {resp.status_code}: {detail}"
            if hint:
                msg += f"\n{hint}"
            raise APIError(msg, status_code=resp.status_code)

        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    # ---- Endpoint helpers -------------------------------------------------

    def me(self) -> Dict:
        """Current authenticated user (/v1/auth/me)."""
        return self.get("/v1/auth/me")

    def public_metrics(self) -> Dict:
        """Public platform metrics (no auth required)."""
        return self.get("/v1/public/metrics")

    def health(self) -> Dict:
        """Backend health check (no auth required)."""
        return self.get("/v1/health/")

    # Bookmarks
    def list_bookmarks(self, params: Optional[Dict] = None) -> list:
        data = self.get("/v1/bookmarks/", params=params)
        return data.get("data", data) if isinstance(data, dict) else data

    def search_bookmarks(self, query: str, params: Optional[Dict] = None) -> list:
        params = dict(params or {})
        params["q"] = query
        data = self.get("/v1/bookmarks/search", params=params)
        return data.get("data", data) if isinstance(data, dict) else data

    def create_bookmark(self, payload: Dict) -> Dict:
        return self.post("/v1/bookmarks/", payload)

    def delete_bookmark(self, bookmark_id: str) -> None:
        return self.delete(f"/v1/bookmarks/{bookmark_id}")

    # Livestreams
    def list_livestreams(self, params: Optional[Dict] = None) -> Any:
        return self.get("/v1/livestreams", params=params)

    def live_livestreams(self, params: Optional[Dict] = None) -> Any:
        return self.get("/v1/livestreams/live", params=params)

    def trending_livestreams(self, params: Optional[Dict] = None) -> Any:
        return self.get("/v1/livestreams/trending", params=params)

    # Developer API keys
    def list_keys(self) -> Dict:
        return self.get("/v1/developer/keys")

    def create_key(self, payload: Dict) -> Dict:
        return self.post("/v1/developer/keys", payload)

    def delete_key(self, key_id: str) -> None:
        return self.delete(f"/v1/developer/keys/{key_id}")


class AuthError(Exception):
    pass


class APIError(Exception):
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code
