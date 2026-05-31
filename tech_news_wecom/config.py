from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    llm_api_key: str
    wecom_webhook: str
    llm_base_url: str | None = None
    llm_model: str = "gpt-4.1-mini"
    timezone: str = "Asia/Shanghai"
    max_items: int = 20


def _load_secrets_file(secrets_path: Path) -> dict:
    if not secrets_path.exists():
        return {}
    return json.loads(secrets_path.read_text(encoding="utf-8"))


def load_settings(repo_root: Path | None = None) -> Settings:
    root = repo_root or Path(__file__).resolve().parents[1]
    secrets = _load_secrets_file(root / "secrets.json")

    llm_api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
        or secrets.get("llm_api_key")
        or secrets.get("openai_api_key")
        or secrets.get("deepseek_api_key")
        or secrets.get("OPENAI_API_KEY")
        or secrets.get("DEEPSEEK_API_KEY")
        or ""
    ).strip()

    llm_base_url = (
        os.getenv("LLM_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or os.getenv("DEEPSEEK_BASE_URL")
        or secrets.get("llm_base_url")
        or secrets.get("openai_base_url")
        or secrets.get("deepseek_base_url")
        or ""
    ).strip()
    llm_base_url = llm_base_url or None

    wecom_webhook = (
        os.getenv("WECOM_WEBHOOK")
        or secrets.get("wecom_webhook")
        or secrets.get("wecom_wenhook")  # typo compatibility
        or ""
    ).strip()

    default_model = "deepseek-chat" if (llm_base_url and "deepseek" in llm_base_url) else "gpt-4.1-mini"
    llm_model = (
        os.getenv("LLM_MODEL")
        or os.getenv("OPENAI_MODEL")
        or os.getenv("DEEPSEEK_MODEL")
        or secrets.get("llm_model")
        or secrets.get("openai_model")
        or secrets.get("deepseek_model")
        or default_model
    ).strip()

    max_items = int(os.getenv("MAX_ITEMS") or secrets.get("max_items") or 20)

    if not llm_api_key:
        raise RuntimeError(
            "Missing LLM API key. Set LLM_API_KEY env (or OPENAI_API_KEY/DEEPSEEK_API_KEY) or secrets.json."
        )
    if not wecom_webhook:
        raise RuntimeError(
            "Missing WeCom webhook. Set WECOM_WEBHOOK env or secrets.json wecom_webhook/wecom_wenhook."
        )

    return Settings(
        llm_api_key=llm_api_key,
        wecom_webhook=wecom_webhook,
        llm_base_url=llm_base_url,
        llm_model=llm_model,
        max_items=max_items,
    )
