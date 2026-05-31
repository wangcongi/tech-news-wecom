from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class RssItem:
    title: str
    link: str
    source: str
    published_at: datetime | None = None


def load_feed_urls(repo_root: Path | None = None) -> list[str]:
    root = repo_root or Path(__file__).resolve().parents[1]
    feeds_path = root / "feeds.txt"
    if not feeds_path.exists():
        return []

    urls: list[str] = []
    for line in feeds_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def _entry_published(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        tm = getattr(entry, key, None)
        if tm:
            return datetime(*tm[:6], tzinfo=timezone.utc)
    return None


def fetch_rss_items(urls: list[str], *, limit: int = 50) -> list[RssItem]:
    import feedparser

    items: list[RssItem] = []

    for url in urls:
        parsed = feedparser.parse(url)
        feed_title = (
            getattr(parsed.feed, "title", None)
            or getattr(parsed.feed, "link", None)
            or url
        )
        for entry in parsed.entries[:limit]:
            title = (getattr(entry, "title", "") or "").strip()
            link = (getattr(entry, "link", "") or "").strip()
            if not title or not link:
                continue
            items.append(
                RssItem(
                    title=title,
                    link=link,
                    source=str(feed_title).strip(),
                    published_at=_entry_published(entry),
                )
            )

    def sort_key(it: RssItem):
        return it.published_at or datetime(1970, 1, 1, tzinfo=timezone.utc)

    items.sort(key=sort_key, reverse=True)
    return items
