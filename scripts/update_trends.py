#!/usr/bin/env python3
"""Erzeugt TrendSelect-Daten aus kostenlosen öffentlichen RSS-/Atom-Feeds."""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "trends.json"
MIN_TRENDS = 10
MAX_TRENDS = 15

FEEDS = (
    {"name": "heise online", "url": "https://www.heise.de/rss/heise-atom.xml", "weight": 9},
    {"name": "tagesschau.de", "url": "https://www.tagesschau.de/xml/rss2/", "weight": 8},
    {"name": "Statistisches Bundesamt", "url": "https://www.destatis.de/SiteGlobals/Functions/RSSFeed/DE/RSSNewsfeed/Aktuell.xml", "weight": 10},
)

CATEGORIES = {
    "KI": ("künstliche intelligenz", " ki ", "chatgpt", "sprachmodell", "llm", "agent", "deepfake", "maschinelles lernen"),
    "Technologie": ("technologie", "software", "chip", "quanten", "robot", "cloud", "cyber", "digital", "internet", "computer", "raumfahrt"),
    "Business": ("wirtschaft", "unternehmen", "markt", "arbeit", "industrie", "startup", "handel", "finanz", "invest", "produktion"),
    "Gesellschaft": ("gesellschaft", "bildung", "demografie", "gesundheit", "bevölkerung", "migration", "medien", "vertrauen", "arbeitsmarkt"),
    "Nachhaltigkeit": ("klima", "energie", "umwelt", "erneuerbar", "recycling", "kreislauf", "wärmepumpe", "emission", "ressourc", "strom"),
}

SYMBOLS = {"KI": "✦", "Technologie": "◇", "Business": "↗", "Gesellschaft": "◎", "Nachhaltigkeit": "↻"}
HORIZONS = {"KI": "Jetzt", "Technologie": "1–3 Jahre", "Business": "Jetzt", "Gesellschaft": "1–3 Jahre", "Nachhaltigkeit": "1–3 Jahre"}
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def clean(value: str | None) -> str:
    text = html.unescape(TAG_RE.sub(" ", value or ""))
    return SPACE_RE.sub(" ", text).strip()


def child_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for child in node.iter():
        if child.tag.rsplit("}", 1)[-1] in names and child.text:
            return child.text.strip()
    return ""


def item_link(node: ET.Element) -> str:
    for child in node.iter():
        if child.tag.rsplit("}", 1)[-1] == "link":
            return child.attrib.get("href") or (child.text or "").strip()
    return ""


def parse_date(raw: str) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        value = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
    return value.replace(tzinfo=value.tzinfo or timezone.utc).astimezone(timezone.utc)


def fetch_feed(feed: dict) -> list[dict]:
    request = urllib.request.Request(feed["url"], headers={"User-Agent": "TrendSelect/1.0 (+GitHub Pages)"})
    with urllib.request.urlopen(request, timeout=25) as response:
        document = ET.fromstring(response.read())
    nodes = [node for node in document.iter() if node.tag.rsplit("}", 1)[-1] in ("item", "entry")]
    result = []
    for node in nodes[:60]:
        title = clean(child_text(node, ("title",)))
        description = clean(child_text(node, ("description", "summary", "content")))
        link = item_link(node)
        published = parse_date(child_text(node, ("pubDate", "published", "updated", "date")))
        if title and link:
            result.append({"title": title, "description": description, "url": link, "published": published, "source": feed["name"], "weight": feed["weight"]})
    return result


def classify(text: str) -> tuple[str | None, int]:
    padded = f" {text.casefold()} "
    scores = {category: sum(1 for word in words if word in padded) for category, words in CATEGORIES.items()}
    category = max(scores, key=scores.get)
    return (category, scores[category]) if scores[category] else (None, 0)


def summary(title: str, description: str, category: str) -> str:
    candidate = description.split(". ", 1)[0].strip()
    if len(candidate) < 45:
        candidate = f"{title} zeigt neue Dynamik im Bereich {category}."
    if len(candidate) > 175:
        candidate = candidate[:172].rsplit(" ", 1)[0] + " …"
    return candidate if candidate.endswith((".", "!", "?", "…")) else candidate + "."


def as_trend(item: dict, category: str, matches: int) -> dict:
    age = max(0, (datetime.now(timezone.utc) - item["published"]).days)
    relevance = min(98, max(68, 72 + item["weight"] + matches * 3 - min(age // 7, 12)))
    stage = "Beschleunigung" if relevance >= 90 else "Wachstum" if relevance >= 82 else "Beobachtung"
    digest = hashlib.sha1(item["url"].encode()).hexdigest()[:10]
    return {
        "id": f"auto-{digest}", "category": category, "title": item["title"][:90],
        "symbol": SYMBOLS[category], "relevance": relevance,
        "date": item["published"].strftime("%d.%m.%Y"),
        "description": summary(item["title"], item["description"], category),
        "insight": f"Dieses Signal wird automatisch aus einer aktuellen Veröffentlichung von {item['source']} abgeleitet. Der Relevanzwert berücksichtigt Aktualität, Quellengewicht und thematische Signalstärke.",
        "stage": stage, "horizon": HORIZONS[category], "source": item["source"], "sourceUrl": item["url"],
    }


def choose(candidates: list[dict], previous: list[dict]) -> list[dict]:
    candidates.sort(key=lambda value: (value["relevance"], value["date"]), reverse=True)
    selected, seen = [], set()

    def add(candidate: dict) -> bool:
        words = frozenset(re.findall(r"\w{4,}", candidate["title"].casefold()))
        if any(len(words & old) / max(1, len(words | old)) > .55 for old in seen):
            return False
        selected.append(candidate)
        seen.add(words)
        return True

    # Der Radar soll nicht durch die Nachrichtenlage einer einzelnen Kategorie
    # dominiert werden: zuerst zwei Signale pro Bereich, danach nach Relevanz.
    for category in CATEGORIES:
        for candidate in (item for item in candidates if item["category"] == category):
            if sum(item["category"] == category for item in selected) >= 2:
                break
            add(candidate)
    for candidate in candidates:
        if len(selected) == MAX_TRENDS:
            break
        if candidate in selected or sum(item["category"] == candidate["category"] for item in selected) >= 4:
            continue
        add(candidate)
    existing_ids = {trend["id"] for trend in selected}
    for trend in previous:
        if len(selected) >= MIN_TRENDS:
            break
        if trend.get("id") not in existing_ids:
            selected.append(trend)
    return selected


def main() -> int:
    previous_payload = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {"trends": []}
    items = []
    for feed in FEEDS:
        try:
            found = fetch_feed(feed)
            print(f"{feed['name']}: {len(found)} Einträge", file=sys.stderr)
            items.extend(found)
        except Exception as error:  # Einzelne Feeds dürfen den Lauf nicht stoppen.
            print(f"WARNUNG {feed['name']}: {error}", file=sys.stderr)
    candidates = []
    for item in items:
        category, matches = classify(f"{item['title']} {item['description']}")
        if category:
            candidates.append(as_trend(item, category, matches))
    trends = choose(candidates, previous_payload.get("trends", []))
    if len(trends) < MIN_TRENDS:
        raise RuntimeError(f"Nur {len(trends)} Trends verfügbar; bestehende Datei bleibt unverändert")
    if trends == previous_payload.get("trends"):
        print("Keine inhaltliche Änderung.")
        return 0
    payload = {"updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "generator": "TrendSelect RSS Radar 1.0", "trends": trends}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(trends)} Trends nach {OUTPUT} geschrieben.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
