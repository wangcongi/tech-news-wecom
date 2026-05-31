from __future__ import annotations

import logging
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import load_settings
from .pipeline import run_once


logger = logging.getLogger("tech_news_wecom")


def run_daily_7am(*, repo_root: Path | None = None) -> None:
    settings = load_settings(repo_root)
    scheduler = BlockingScheduler(timezone=settings.timezone)

    trigger = CronTrigger(hour=9, minute=0, timezone=settings.timezone)
    scheduler.add_job(
        lambda: run_once(settings, repo_root=repo_root),
        trigger=trigger,
        id="daily_briefing",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60 * 60,
    )

    logger.info("Scheduler started: daily 09:00 (%s)", settings.timezone)
    scheduler.start()
