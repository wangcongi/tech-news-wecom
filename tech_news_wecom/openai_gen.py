from __future__ import annotations

from dataclasses import dataclass

from .rss import RssItem


@dataclass(frozen=True)
class Briefing:
    title: str
    markdown: str


SYSTEM_PROMPT = """你是一名科技媒体编辑。请把给定的新闻条目整理成中文《科技早报》。
要求：
1) 输出使用 Markdown，结构清晰，适合企业微信群机器人展示。
2) 不要编造事实；只基于给定标题/来源/链接做摘要推断，避免具体数字/引号除非标题中明确。
3) 按主题分组（AI/芯片、互联网、消费电子、安全、创业投融资、其他等），每组 2-6 条要点。
4) 每条要点必须包含可点击的原文链接，格式严格为：
   - **一句话摘要**（来源） [原文](URL)
   其中 URL 必须是输入里给出的链接，禁止写“链接”两个字占位。
5) 末尾给出 3 条“今日关注”要点（更具趋势意义），同样带链接。
6) 全文控制在 900~1600 中文字符左右，避免过长。
"""


def _items_to_prompt(items: list[RssItem]) -> str:
    lines = []
    for idx, it in enumerate(items, start=1):
        # 提供可直接复用的 URL，减少模型漏链接/写占位的概率
        lines.append(
            "\n".join(
                [
                    f"{idx}. 标题：{it.title}",
                    f"   来源：{it.source}",
                    f"   链接：{it.link}",
                    f"   可复用格式：- **（请写一句话摘要）**（{it.source}） [原文]({it.link})",
                ]
            )
        )
    return "\n".join(lines)


def generate_briefing(
    *,
    api_key: str,
    base_url: str | None,
    model: str,
    items: list[RssItem],
    date_label: str,
) -> Briefing:
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    user_prompt = f"日期：{date_label}\n\n新闻条目：\n{_items_to_prompt(items)}\n"
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
    return Briefing(title=title, markdown=content)
