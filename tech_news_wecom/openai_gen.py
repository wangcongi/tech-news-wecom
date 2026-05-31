from __future__ import annotations

from dataclasses import dataclass

from .rss import RssItem


@dataclass(frozen=True)
class Briefing:
    title: str
    markdown: str


SYSTEM_PROMPT = """你是一名科技媒体编辑与买方研究助理。请把给定的新闻条目整理成中文《科技早报（精选5条）》。

精选逻辑（请显式执行“打分/权衡”，但不要输出分数细节）：
1) 可能引起行业资本剧烈反应的程度（催化剂强弱、情绪冲击、监管变化）。
2) 技术创新程度（方法/产品/标准的“代际变化”）。
3) 产业供需变化程度（产能、价格、订单、出货、渠道、库存、瓶颈）。
4) 只优先关注顶尖个体公司/机构（能代表行业趋势的龙头、关键基础设施、关键平台）。
5) 全球资本关注程度（欧美大型媒体/机构集中报道、影响全球链条）。
6) 国内资本关注程度（更贴近国内产业链/政策/投融资）。
7) 同花顺新兴概念热度（优先选择与输入条目命中的“概念关键词”强相关的新闻）。
8) 如输入包含上证指数大阳/大阴监控信息，则优先纳入并解释主要原因（不要编造原因；没有依据就说“待观察”）。

输出要求：
- 使用 Markdown，适合企业微信展示。
- 只输出 5 条要点（不分组、不加“今日关注”）。
- 不要编造事实；只基于给定标题/来源/链接做摘要推断，避免具体数字/引号除非标题中明确。
- 每条要点必须包含可点击原文链接，格式严格为：
  - **一句话摘要**（来源） [原文](URL)
  URL 必须来自输入，禁止写“原文/链接”占位但不带 URL。
- 内容精炼，尽量控制在 900 中文字符以内。
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
    top_n: int = 5,
    extra_context: str | None = None,
) -> Briefing:
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    extra = f"\n\n补充上下文（可能为空）：\n{extra_context}\n" if extra_context else ""
    user_prompt = (
        f"日期：{date_label}\n"
        f"请只挑选并输出 {top_n} 条。\n"
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
    return Briefing(title=title, markdown=content)
