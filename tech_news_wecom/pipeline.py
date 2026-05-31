from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import Settings
from .concepts import filter_items_by_concepts, load_concepts
from .openai_gen import generate_briefing
from .rss import fetch_rss_items, load_feed_urls, RssItem
from .storage import SeenStore
from .wecom import send_markdown
from .wecom_app import WeComAppClient


def _today_label_shanghai() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")


def _limit_wecom_markdown(content: str, *, max_len: int = 4096) -> str:
    if len(content) <= max_len:
        return content
    suffix = "\n\n> （消息过长，已自动截断）"
    keep = max_len - len(suffix)
    if keep <= 0:
        return content[:max_len]
    trimmed = content[:keep].rstrip()
    return trimmed + suffix


def run_once(settings: Settings, *, repo_root: Path | None = None) -> dict:
    root = repo_root or Path(__file__).resolve().parents[1]
    urls = load_feed_urls(root)
    if not urls:
        raise RuntimeError("No RSS feeds configured in feeds.txt")

    all_items = fetch_rss_items(urls, limit=50)
    concepts = load_concepts(root, settings.concepts_path)
    filtered_items, buckets = filter_items_by_concepts(all_items, concepts)

    store = SeenStore(db_path=root / "data" / "seen.sqlite3")
    new_links = set(store.filter_new([it.link for it in (filtered_items or all_items)]))
    new_items: list[RssItem] = [it for it in (filtered_items or all_items) if it.link in new_links]

    base_pool = filtered_items or all_items
    selected = (new_items or base_pool)[: settings.max_items]
    date_label = _today_label_shanghai()
    briefing = generate_briefing(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        items=selected,
        date_label=date_label,
        top_n=settings.briefing_top_n,
    )

    header = f"## {briefing.title}\n\n"
    content = _limit_wecom_markdown(header + briefing.markdown)
    if settings.wecom_mode == "webhook":
        assert settings.wecom_webhook
        send_markdown(settings.wecom_webhook, content)
    else:
        assert settings.wecom_corpid and settings.wecom_corpsecret and settings.wecom_agentid
        client = WeComAppClient(corpid=settings.wecom_corpid, corpsecret=settings.wecom_corpsecret)
        client.send_markdown(
            agentid=settings.wecom_agentid,
            markdown=content,
            touser=settings.wecom_touser,
            toparty=settings.wecom_toparty,
            totag=settings.wecom_totag,
        )

    return {
        "feeds": len(urls),
        "items_total": len(all_items),
        "items_filtered": len(filtered_items),
        "items_new": len(new_items),
        "items_used": len(selected),
        "date": date_label,
        "concepts": [c.name for c in concepts],
        "concept_buckets": {k: len(v) for k, v in buckets.items()} if buckets else {},
    }
