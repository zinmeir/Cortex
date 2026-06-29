import requests
from typing import Dict, Any
from app.utils.logger import get_logger

logger = get_logger("tools.api_client")

_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254"}


class APIClient:
    """Generic HTTP client for external API calls."""

    TIMEOUT = 30

    def call(
        self,
        url: str,
        method: str = "GET",
        headers: Dict[str, str] | None = None,
        params: Dict[str, Any] | None = None,
        body: Dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> Dict[str, Any]:
        for blocked in _BLOCKED_HOSTS:
            if blocked in url:
                return {"success": False, "error": f"Blocked internal address in URL: {url}"}

        try:
            resp = requests.request(
                method=method.upper(),
                url=url,
                headers=headers or {},
                params=params,
                json=body,
                timeout=timeout or self.TIMEOUT,
            )
            try:
                data = resp.json()
                content_type = "json"
            except Exception:
                data = resp.text[:5000]
                content_type = "text"

            return {
                "success": resp.ok,
                "status_code": resp.status_code,
                "content_type": content_type,
                "data": data,
                "url": str(resp.url),
            }
        except requests.Timeout:
            return {"success": False, "error": f"Timed out after {timeout or self.TIMEOUT}s"}
        except requests.ConnectionError as exc:
            return {"success": False, "error": f"Connection error: {exc}"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


api_client = APIClient()
