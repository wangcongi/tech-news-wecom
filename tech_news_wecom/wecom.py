from __future__ import annotations

def send_markdown(webhook: str, markdown: str) -> None:
    import requests

    payload = {"msgtype": "markdown", "markdown": {"content": markdown}}
    r = requests.post(webhook, json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()
    if data.get("errcode") not in (0, "0", None):
        raise RuntimeError(f"WeCom webhook error: {data}")
