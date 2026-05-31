from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import Settings
from .concepts import filter_items_by_concepts, load_concepts
from .market import build_market_context
from .openai_gen import generate_briefing
from .rss import fetch_rss_items, load_feed_urls, RssItem
from .storage import SeenStore
from .wecom import send_markdown
from .wecom_app import WeComAppClient


def _today_label_shanghai() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")


def _briefing_window_shanghai(*, end_hour: int) -> tuple[datetime, datetime]:
    tz = ZoneInfo("Asia/Shanghai")
    now = datetime.now(tz)
    today_end = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    end = today_end if now >= today_end else (today_end - timedelta(days=1))
    start = end - timedelta(days=1)
    return start, end


def _filter_by_time_window(
    items: list[RssItem],
    *,
    start: datetime,
    end: datetime,
) -> tuple[list[RssItem], int]:
    """
    Keep items with published_at in [start, end).
    If published_at is missing, exclude by default.
    Returns (filtered_items, missing_published_count).
    """
    tz = ZoneInfo("Asia/Shanghai")
    filtered: list[RssItem] = []
    missing = 0
    for it in items:
        if not it.published_at:
            missing += 1
            continue
        dt = it.published_at.astimezone(tz)
        if start <= dt < end:
            filtered.append(it)
    return filtered, missing


def _limit_wecom_markdown(content: str, *, max_len: int = 4096) -> str:
    if len(content) <= max_len:
        return content
    suffix = "\n\n> （消息过长，已自动截断）"
    keep = max_len - len(suffix)
    if keep <= 0:
        return content[:max_len]
    trimmed = content[:keep].rstrip()
    return trimmed + suffix


def _disclaimer_markdown() -> str:
    return (
        "\n\n---\n"
        "> 免责声明：本早报为基于公开 RSS 标题的自动化整理与摘要，可能存在遗漏/误差；"
        "仅供信息参考，不构成任何投资建议或收益保证。请以原文为准并自行判断风险。"
    )


def run_once(settings: Settings, *, repo_root: Path | None = None) -> dict:
    root = repo_root or Path(__file__).resolve().parents[1]
    urls = load_feed_urls(root)
    if not urls:
        raise RuntimeError("No RSS feeds configured in feeds.txt")

    all_items = fetch_rss_items(urls, limit=50)
    window_start, window_end = _briefing_window_shanghai(end_hour=settings.briefing_window_end_hour)
    window_items, missing_published = _filter_by_time_window(
        all_items, start=window_start, end=window_end
    )
    concepts = load_concepts(root, settings.concepts_path)
    filtered_items, buckets = filter_items_by_concepts(window_items, concepts)

    store = SeenStore(db_path=root / "data" / "seen.sqlite3")
    new_links = set(store.filter_new([it.link for it in (filtered_items or all_items)]))
    base_all = filtered_items or window_items
    if not base_all:
        base_all = all_items
    new_links = set(store.filter_new([it.link for it in base_all]))
    new_items: list[RssItem] = [it for it in base_all if it.link in new_links]

    base_pool = filtered_items or window_items or all_items
    selected = (new_items or base_pool)[: settings.max_items]
    date_label = _today_label_shanghai()
    market_context = build_market_context()
    briefing = generate_briefing(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        items=selected,
        date_label=date_label,
        top_n=settings.briefing_top_n,
        extra_context=market_context,
    )

    header = f"## {briefing.title}\n\n"
    content = _limit_wecom_markdown(header + briefing.markdown + _disclaimer_markdown())
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
        "items_in_window": len(window_items),
        "items_filtered": len(filtered_items),
        "items_new": len(new_items),
        "items_used": len(selected),
        "date": date_label,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "items_missing_published": missing_published,
        "concepts": [c.name for c in concepts],
        "concept_buckets": {k: len(v) for k, v in buckets.items()} if buckets else {},
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "briefing_top_n": settings.briefing_top_n,
        "briefing_window_end_hour": settings.briefing_window_end_hour,
    }
