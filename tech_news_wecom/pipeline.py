from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import Settings
from .openai_gen import generate_briefing
from .rss import fetch_rss_items, load_feed_urls, RssItem
from .storage import SeenStore
from .wecom import send_markdown


def _today_label_shanghai() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")


def run_once(settings: Settings, *, repo_root: Path | None = None) -> dict:
    root = repo_root or Path(__file__).resolve().parents[1]
    urls = load_feed_urls(root)
    if not urls:
        raise RuntimeError("No RSS feeds configured in feeds.txt")

    all_items = fetch_rss_items(urls, limit=50)

    store = SeenStore(db_path=root / "data" / "seen.sqlite3")
    new_links = set(store.filter_new([it.link for it in all_items]))
    new_items: list[RssItem] = [it for it in all_items if it.link in new_links]

    selected = (new_items or all_items)[: settings.max_items]
    date_label = _today_label_shanghai()
    briefing = generate_briefing(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        items=selected,
        date_label=date_label,
    )

    header = f"## {briefing.title}\n\n"
    send_markdown(settings.wecom_webhook, header + briefing.markdown)

    return {
        "feeds": len(urls),
        "items_total": len(all_items),
        "items_new": len(new_items),
        "items_used": len(selected),
        "date": date_label,
    }
