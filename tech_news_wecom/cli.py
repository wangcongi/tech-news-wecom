from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_settings
from .pipeline import run_once


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tech-news-wecom")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("run-once", help="立即抓取并推送一次")
    sub.add_parser("schedule", help="常驻：每天北京时间07:00执行")

    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]

    if args.cmd == "run-once":
        settings = load_settings(repo_root)
        result = run_once(settings, repo_root=repo_root)
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.cmd == "schedule":
        from .scheduler import run_daily_7am

        run_daily_7am(repo_root=repo_root)
        return 0

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
