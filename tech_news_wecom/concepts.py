from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .rss import RssItem


@dataclass(frozen=True)
class Concept:
    name: str
    keywords: list[str]


def load_concepts(repo_root: Path, concepts_path: str | None) -> list[Concept]:
    if not concepts_path:
        return []
    path = (repo_root / concepts_path).resolve()
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    concepts: list[Concept] = []
    for c in data.get("concepts", []):
        name = (c.get("name") or "").strip()
        keywords = [str(k).strip() for k in (c.get("keywords") or []) if str(k).strip()]
        if name and keywords:
            concepts.append(Concept(name=name, keywords=keywords))
    return concepts


def filter_items_by_concepts(items: list[RssItem], concepts: list[Concept]) -> tuple[list[RssItem], dict[str, list[RssItem]]]:
    if not concepts:
        return items, {}

    buckets: dict[str, list[RssItem]] = {c.name: [] for c in concepts}
    selected: list[RssItem] = []

    for it in items:
        hay = f"{it.title} {it.source}".lower()
        matched_names: list[str] = []
        for c in concepts:
            if any(k.lower() in hay for k in c.keywords):
                matched_names.append(c.name)
        if not matched_names:
            continue
        selected.append(it)
        for name in matched_names:
            buckets[name].append(it)

    return selected, buckets

