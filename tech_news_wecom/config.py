from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    wecom_webhook: str
    openai_model: str = "gpt-4.1-mini"
    timezone: str = "Asia/Shanghai"
    max_items: int = 20


def _load_secrets_file(secrets_path: Path) -> dict:
    if not secrets_path.exists():
        return {}
    return json.loads(secrets_path.read_text(encoding="utf-8"))


def load_settings(repo_root: Path | None = None) -> Settings:
    root = repo_root or Path(__file__).resolve().parents[1]
    secrets = _load_secrets_file(root / "secrets.json")

    openai_api_key = (
        os.getenv("OPENAI_API_KEY")
        or secrets.get("openai_api_key")
        or secrets.get("OPENAI_API_KEY")
        or ""
    ).strip()

    wecom_webhook = (
        os.getenv("WECOM_WEBHOOK")
        or secrets.get("wecom_webhook")
        or secrets.get("wecom_wenhook")  # typo compatibility
        or ""
    ).strip()

    openai_model = (
        os.getenv("OPENAI_MODEL")
        or secrets.get("openai_model")
        or "gpt-4.1-mini"
    ).strip()

    max_items = int(os.getenv("MAX_ITEMS") or secrets.get("max_items") or 20)

    if not openai_api_key:
        raise RuntimeError(
            "Missing OpenAI API key. Set OPENAI_API_KEY env or secrets.json openai_api_key."
        )
    if not wecom_webhook:
        raise RuntimeError(
            "Missing WeCom webhook. Set WECOM_WEBHOOK env or secrets.json wecom_webhook/wecom_wenhook."
        )

    return Settings(
        openai_api_key=openai_api_key,
        wecom_webhook=wecom_webhook,
        openai_model=openai_model,
        max_items=max_items,
    )

