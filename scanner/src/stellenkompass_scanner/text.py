from __future__ import annotations

import html
import re
from datetime import UTC, datetime
from html.parser import HTMLParser

_BLOCK_TAGS = {"p", "br", "li", "div", "h1", "h2", "h3", "h4", "tr", "ul", "ol"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in _BLOCK_TAGS:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in _BLOCK_TAGS:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def html_to_text(raw: str | None) -> str:
    """Plain text from HTML. Handles HTML that was escaped once more (Greenhouse does this)."""
    if not raw:
        return ""
    if "&lt;" in raw and "<" not in raw:
        raw = html.unescape(raw)
    parser = _TextExtractor()
    parser.feed(raw)
    parser.close()
    return normalize_space("".join(parser.parts))


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def snippet(text: str, limit: int = 300) -> str:
    text = normalize_space(text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut + "…"


def iso_date(value: str | int | float | None) -> str:
    """ISO-8601 UTC timestamp from an ISO string, unix seconds or unix milliseconds."""
    if value in (None, ""):
        return ""
    try:
        if isinstance(value, int | float):
            seconds = value / 1000 if value > 10**11 else value
            dt = datetime.fromtimestamp(seconds, tz=UTC)
        else:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
    except (ValueError, OverflowError, OSError):
        return ""
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
