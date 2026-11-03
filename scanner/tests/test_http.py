import httpx
import pytest

from stellenkompass_scanner import http
from stellenkompass_scanner.http import HttpFetcher, retry_after


@pytest.mark.parametrize(
    ("value", "seconds"),
    [(None, 0.0), ("5", 5.0), ("999", http.MAX_RETRY_AFTER), ("-3", 0.0), ("Wed, 21 Oct", 0.0)],
)
def test_retry_after(value, seconds):
    assert retry_after(value) == seconds


def test_429_waits_for_retry_after_then_succeeds(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(http.time, "sleep", sleeps.append)
    replies = iter(
        [httpx.Response(429, headers={"Retry-After": "7"}), httpx.Response(200, json=[1])]
    )
    fetcher = HttpFetcher(pause=0.1)
    fetcher._client = httpx.Client(transport=httpx.MockTransport(lambda request: next(replies)))
    assert fetcher.get_json("https://example.org") == [1]
    assert sleeps == [0.1, 7.0]


def test_gives_up_after_retries(monkeypatch):
    monkeypatch.setattr(http.time, "sleep", lambda s: None)
    fetcher = HttpFetcher(pause=0, retries=2)
    fetcher._client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    with pytest.raises(httpx.HTTPStatusError, match="HTTP 503"):
        fetcher.get_json("https://example.org")
