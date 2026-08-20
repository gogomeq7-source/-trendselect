#!/usr/bin/env python3
"""Import approved Awin product feeds into the static TrendSelect catalogue."""

from __future__ import annotations

import csv
import gzip
import hashlib
import html
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "products.json"
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
FALSE_VALUES = {"0", "false", "no", "nein", "out of stock", "nicht auf lager"}


def first(row: dict[str, str], *keys: str) -> str:
    lowered = {str(key).strip().lower(): (value or "").strip() for key, value in row.items()}
    return next((lowered[key.lower()] for key in keys if lowered.get(key.lower())), "")


def clean_text(value: str, limit: int) -> str:
    text = html.unescape(TAG_RE.sub(" ", value or ""))
    text = SPACE_RE.sub(" ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def valid_url(value: str) -> str:
    try:
        parsed = urlparse(value)
        return value if parsed.scheme in {"http", "https"} and parsed.netloc else ""
    except ValueError:
        return ""


def decimal_value(value: str) -> float | None:
    normalized = (value or "").strip().replace("'", "").replace(" ", "")
    if not normalized:
        return None
    if "," in normalized and "." not in normalized:
        normalized = normalized.replace(",", ".")
    normalized = re.sub(r"[^0-9.\-]", "", normalized)
    try:
        number = Decimal(normalized)
        return float(number) if number >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def map_product(row: dict[str, str]) -> dict | None:
    title = clean_text(first(row, "product_name", "name", "title"), 140)
    affiliate_url = valid_url(first(row, "aw_deep_link", "deep_link", "affiliate_url"))
    image = valid_url(first(row, "aw_image_url", "large_image", "merchant_image_url", "image_url"))
    price = decimal_value(first(row, "search_price", "store_price", "price"))
    currency = first(row, "currency", "currency_code").upper()
    stock = first(row, "in_stock", "stock_status", "availability").lower()
    if not title or not affiliate_url or not image or price is None or len(currency) != 3 or stock in FALSE_VALUES:
        return None
    merchant = clean_text(first(row, "merchant_name", "advertiser_name"), 80)
    raw_id = first(row, "aw_product_id", "product_id", "merchant_product_id", "sku")
    stable = "|".join((first(row, "merchant_id", "advertiser_id"), raw_id, title, affiliate_url))
    old_price = decimal_value(first(row, "product_price_old", "rrp_price", "old_price"))
    product = {
        "id": hashlib.sha256(stable.encode("utf-8")).hexdigest()[:20],
        "title": title,
        "description": clean_text(first(row, "product_short_description", "description"), 220),
        "category": clean_text(first(row, "category_name", "merchant_category", "product_type"), 70) or "Weitere",
        "merchant": merchant,
        "image": image,
        "price": price,
        "currency": currency,
        "affiliateUrl": affiliate_url,
    }
    if old_price is not None and old_price > price:
        product["originalPrice"] = old_price
    return product


def read_feed(url: str) -> list[dict]:
    request = Request(url, headers={"User-Agent": "TrendSelect-Product-Importer/1.0"})
    with urlopen(request, timeout=90) as response:
        payload = response.read()
        encoding = response.headers.get("Content-Encoding", "").lower()
    if encoding == "gzip" or payload[:2] == b"\x1f\x8b":
        payload = gzip.decompress(payload)
    text = payload.decode("utf-8-sig", errors="replace")
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    return [product for row in csv.DictReader(io.StringIO(text), dialect=dialect) if (product := map_product(row))]


def main() -> int:
    urls = [line.strip() for line in os.getenv("AWIN_PRODUCT_FEED_URLS", "").splitlines() if line.strip()]
    if not urls:
        print("AWIN_PRODUCT_FEED_URLS ist nicht gesetzt; vorhandener Produktkatalog bleibt unverändert.")
        return 0
    limit = max(1, min(int(os.getenv("PRODUCT_LIMIT", "5000")), 20000))
    products: dict[str, dict] = {}
    failures = 0
    for url in urls:
        try:
            for product in read_feed(url):
                products[product["id"]] = product
        except Exception as exc:  # Continue with other approved feeds.
            failures += 1
            print(f"Feed konnte nicht importiert werden: {type(exc).__name__}", file=sys.stderr)
    if not products:
        print("Keine gültigen Produkte empfangen; vorhandener Produktkatalog bleibt unverändert.", file=sys.stderr)
        return 1 if failures else 0
    catalogue = {
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": "Awin",
        "products": sorted(products.values(), key=lambda item: (item["category"].casefold(), item["title"].casefold()))[:limit],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(catalogue['products'])} Produkte aktualisiert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
