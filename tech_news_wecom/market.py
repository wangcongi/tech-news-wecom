from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndexSnapshot:
    name: str
    code: str
    price: float | None
    pct: float | None


def fetch_sse_composite_snapshot() -> IndexSnapshot | None:
    """
    Fetch 上证指数（000001）快照。
    使用腾讯行情公开接口（不保证稳定），失败则返回 None。
    """
    import requests

    # s_sh000001: 上证指数（简要行情）
    url = "https://qt.gtimg.cn/q=s_sh000001"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    text = r.text.strip()
    # Example: v_s_sh000001="1~上证指数~000001~3500.00~+1.23~...";
    if "=" not in text or "~" not in text:
        return None
    try:
        payload = text.split("=", 1)[1].strip().strip(";").strip('"')
        parts = payload.split("~")
        name = parts[1]
        code = parts[2]
        price = float(parts[3]) if parts[3] else None
        pct = float(parts[4]) if parts[4] else None
        return IndexSnapshot(name=name, code=code, price=price, pct=pct)
    except Exception:
        return None


def build_market_context(*, threshold_pct: float = 2.0) -> str | None:
    snap = fetch_sse_composite_snapshot()
    if not snap or snap.pct is None:
        return None
    if abs(snap.pct) < threshold_pct:
        return None
    direction = "大阳" if snap.pct > 0 else "大阴"
    return (
        f"上证指数监控：今日 {direction}（{snap.pct:+.2f}%），"
        f"请尝试用输入新闻解释主要原因；如无法从输入中找到依据，请明确写“仅从本次输入新闻无法确定主要原因，待观察”。"
    )

