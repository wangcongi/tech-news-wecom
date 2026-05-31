from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.parse import urlparse

from .rss import RssItem


@dataclass(frozen=True)
class Briefing:
    title: str
    markdown: str


SYSTEM_PROMPT = """你是一名科技媒体编辑与买方研究助理。你将从输入新闻条目中挑选最重要的 N 条，并输出严格 JSON，供程序渲染推送。

精选逻辑（请执行“打分/权衡”，但不要输出分数）：
1) 可能引起行业资本剧烈反应的程度（催化剂强弱、情绪冲击、监管变化）。
2) 技术创新程度（方法/产品/标准的“代际变化”）。
3) 产业供需变化程度（产能、价格、订单、出货、渠道、库存、瓶颈）。
4) 只优先关注顶尖个体公司/机构（能代表行业趋势的龙头、关键基础设施、关键平台）。
5) 全球资本关注程度（欧美大型媒体/机构集中报道、影响全球链条）。
6) 国内资本关注程度（更贴近国内产业链/政策/投融资）。
7) 同花顺新兴概念热度（优先选择与输入条目命中的“概念关键词”强相关的新闻）。
8) 如输入包含上证指数大阳/大阴监控信息，则优先纳入并解释主要原因（不要编造原因；没有依据就说“待观察”）。

输出格式（必须是可被 json.loads 解析的 JSON，禁止输出 Markdown/解释/多余文字）：
{
  "picks": [
    { "item": 1, "summary": "一句话中文摘要（不含链接）" }
  ]
}
约束：
- picks 长度必须等于 N（由用户消息指定）。
- item 是输入新闻条目编号（从 1 开始）。
- summary 精炼客观，不要编造数据或引号。
"""


def _items_to_prompt(items: list[RssItem]) -> str:
    lines = []
    for idx, it in enumerate(items, start=1):
        # 提供明确编号，便于模型选择 item
        lines.append(
            "\n".join(
                [
                    f"{idx}. 标题：{it.title}",
                    f"   来源：{it.source}",
                    f"   链接：{it.link}",
                ]
            )
        )
    return "\n".join(lines)

def _safe_source_label(source: str) -> str:
    s = (source or "").strip()
    if not s:
        return "来源"
    return s


def _host_label(url: str) -> str:
    try:
        host = urlparse(url).netloc
        return host or url
    except Exception:
        return url


def _render_markdown(items: list[RssItem], picks: list[dict], *, top_n: int) -> str:
    used = set()
    lines: list[str] = []
    for p in picks:
        if len(lines) >= top_n:
            break
        try:
            idx = int(p.get("item"))
        except Exception:
            continue
        if idx < 1 or idx > len(items) or idx in used:
            continue
        used.add(idx)
        it = items[idx - 1]
        summary = str(p.get("summary") or "").strip()
        if not summary:
            summary = it.title
        lines.append(f"- **{summary}**（{_safe_source_label(it.source)}） [原文]({it.link})")

    # fallback: top_n by order if model output invalid
    if len(lines) < top_n:
        for it in items:
            if len(lines) >= top_n:
                break
            lines.append(f"- **{it.title}**（{_safe_source_label(it.source)}） [原文]({it.link})")
    return "\n".join(lines[:top_n]).strip()


def generate_briefing(
    *,
    api_key: str,
    base_url: str | None,
    model: str,
    items: list[RssItem],
    date_label: str,
    top_n: int = 5,
    extra_context: str | None = None,
) -> Briefing:
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    extra = f"\n\n补充上下文（可能为空）：\n{extra_context}\n" if extra_context else ""
    user_prompt = (
        f"日期：{date_label}\n"
        f"请只挑选并输出 {top_n} 条，并按要求输出 JSON。\n"
        f"{extra}"
        f"\n新闻条目：\n{_items_to_prompt(items)}\n"
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )
    content = (resp.choices[0].message.content or "").strip()
    title = f"科技早报（{date_label}）"
    picks: list[dict] = []
    try:
        data = json.loads(content)
        if isinstance(data, dict) and isinstance(data.get("picks"), list):
            picks = [p for p in data["picks"] if isinstance(p, dict)]
    except Exception:
        picks = []

    markdown = _render_markdown(items, picks, top_n=top_n)
    return Briefing(title=title, markdown=markdown)
