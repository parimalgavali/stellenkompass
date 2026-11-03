from __future__ import annotations

import time
from typing import Any, Protocol

import httpx

USER_AGENT = (
    "Stellenkompass/0.1 (personal job radar; +https://github.com/parimalgavali/stellenkompass)"
)


class Fetcher(Protocol):
    def get_json(self, url: str, params: dict | None = None) -> Any: ...
    def get_text(self, url: str, params: dict | None = None) -> str: ...


class HttpFetcher:
    """Polite HTTP client: one shared connection pool, a pause between requests, few retries."""

    def __init__(self, pause: float = 0.5, retries: int = 2, timeout: float = 30.0) -> None:
        self.pause = pause
        self.retries = retries
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT, "Accept": "application/json, text/xml;q=0.9"},
            timeout=timeout,
            follow_redirects=True,
        )

    def _get(self, url: str, params: dict | None) -> httpx.Response:
        last: Exception | None = None
        for attempt in range(self.retries + 1):
            time.sleep(self.pause if attempt == 0 else self.pause * 4 * attempt)
            try:
                response = self._client.get(url, params=params)
                if response.status_code in (429, 500, 502, 503, 504):
                    last = httpx.HTTPStatusError(
                        f"HTTP {response.status_code}", request=response.request, response=response
                    )
                    continue
                response.raise_for_status()
                return response
            except httpx.TransportError as exc:
                last = exc
        assert last is not None
        raise last

    def get_json(self, url: str, params: dict | None = None) -> Any:
        return self._get(url, params).json()

    def get_text(self, url: str, params: dict | None = None) -> str:
        return self._get(url, params).text

    def close(self) -> None:
        self._client.close()
