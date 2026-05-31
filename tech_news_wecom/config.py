from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    llm_api_key: str
    wecom_mode: str  # webhook | app
    wecom_webhook: str | None = None
    wecom_corpid: str | None = None
    wecom_corpsecret: str | None = None
    wecom_agentid: int | None = None
    wecom_touser: str | None = None
    wecom_toparty: str | None = None
    wecom_totag: str | None = None
    llm_base_url: str | None = None
    llm_model: str = "gpt-4.1-mini"
    timezone: str = "Asia/Shanghai"
    max_items: int = 20
    concepts_path: str | None = "concepts.json"
    briefing_top_n: int = 10
    briefing_window_end_hour: int = 9


def _load_secrets_file(secrets_path: Path) -> dict:
    if not secrets_path.exists():
        return {}
    return json.loads(secrets_path.read_text(encoding="utf-8"))


def load_settings(repo_root: Path | None = None) -> Settings:
    root = repo_root or Path(__file__).resolve().parents[1]
    secrets = _load_secrets_file(root / "secrets.json")

    wecom_mode = (os.getenv("WECOM_MODE") or secrets.get("wecom_mode") or "webhook").strip().lower()

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
    ).strip() or None

    wecom_corpid = (os.getenv("WECOM_CORPID") or secrets.get("wecom_corpid") or "").strip() or None
    wecom_corpsecret = (
        os.getenv("WECOM_CORPSECRET") or secrets.get("wecom_corpsecret") or ""
    ).strip() or None
    agentid_raw = (os.getenv("WECOM_AGENTID") or secrets.get("wecom_agentid") or "").strip()
    wecom_agentid = int(agentid_raw) if agentid_raw else None
    wecom_touser = (os.getenv("WECOM_TOUSER") or secrets.get("wecom_touser") or "").strip() or None
    wecom_toparty = (os.getenv("WECOM_TOPARTY") or secrets.get("wecom_toparty") or "").strip() or None
    wecom_totag = (os.getenv("WECOM_TOTAG") or secrets.get("wecom_totag") or "").strip() or None

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
    briefing_top_n = int(os.getenv("BRIEFING_TOP_N") or secrets.get("briefing_top_n") or 10)
    briefing_window_end_hour = int(
        os.getenv("BRIEFING_WINDOW_END_HOUR") or secrets.get("briefing_window_end_hour") or 9
    )
    concepts_path = (
        os.getenv("CONCEPTS_PATH")
        or secrets.get("concepts_path")
        or "concepts.json"
    ).strip()
    concepts_path = concepts_path or None

    if not llm_api_key:
        raise RuntimeError(
            "Missing LLM API key. Set LLM_API_KEY env (or OPENAI_API_KEY/DEEPSEEK_API_KEY) or secrets.json."
        )

    if wecom_mode not in ("webhook", "app"):
        raise RuntimeError("Invalid WECOM_MODE. Use 'webhook' or 'app'.")

    if wecom_mode == "webhook":
        if not wecom_webhook:
            raise RuntimeError(
                "Missing WeCom webhook. Set WECOM_WEBHOOK env or secrets.json wecom_webhook/wecom_wenhook."
            )
    else:
        if not (wecom_corpid and wecom_corpsecret and wecom_agentid):
            raise RuntimeError(
                "Missing WeCom app credentials. Need WECOM_CORPID, WECOM_CORPSECRET, WECOM_AGENTID."
            )
        if not (wecom_touser or wecom_toparty or wecom_totag):
            raise RuntimeError(
                "Missing WeCom app recipients. Set one of WECOM_TOUSER / WECOM_TOPARTY / WECOM_TOTAG."
            )

    return Settings(
        llm_api_key=llm_api_key,
        wecom_mode=wecom_mode,
        wecom_webhook=wecom_webhook,
        wecom_corpid=wecom_corpid,
        wecom_corpsecret=wecom_corpsecret,
        wecom_agentid=wecom_agentid,
        wecom_touser=wecom_touser,
        wecom_toparty=wecom_toparty,
        wecom_totag=wecom_totag,
        llm_base_url=llm_base_url,
        llm_model=llm_model,
        max_items=max_items,
        concepts_path=concepts_path,
        briefing_top_n=briefing_top_n,
        briefing_window_end_hour=briefing_window_end_hour,
    )
