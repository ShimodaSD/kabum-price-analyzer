"""Checks the day's collection: the total the API declares, the repeated products and the total the store page shows.

The API pagination loses products: the default ordering has ties, and each page breaks them differently.
Some products come in two pages and others in none. The check measures how much was missing and records the number."""

import csv
import json
import re
import time
from collections import Counter
from pathlib import Path

import httpx

from collect import HEADERS, WAIT, day_folder, log
from read import read_day

STORE_PAGE = "https://www.kabum.com.br/hardware/placa-de-video-vga"
MIN_COVERAGE = 0.90  # in the 2026-11-14 runs coverage stayed between 92% and 100%
CHECK_LOG = Path("dados/conferencia.csv")  # one row per collection day: what was missing gets written down
COLUMNS = ["dia", "lidos", "diferentes", "repetidos", "declarado", "loja", "cobertura"]


def declared_total(folder):
    """The total the API itself claims to have, from the first saved page."""
    first = json.loads((Path(folder) / "pagina-001.json").read_text(encoding="utf-8"))
    return first["meta"]["total_items_count"]


def store_page(folder):
    """The category page HTML, saved in the day folder. Requested once a day, like the API pages."""
    target = Path(folder) / "loja.html"
    if target.exists():
        log.info("already have %s, not requesting it again", target)
        return target.read_text(encoding="utf-8")
    response = httpx.get(STORE_PAGE, headers={**HEADERS, "Accept": "text/html"}, timeout=30)
    time.sleep(WAIT)
    if response.status_code != 200:
        log.warning("the store page answered %s; the check continues with the API total only", response.status_code)
        return None
    target.write_bytes(response.content)
    return response.text


def page_total(html):
    """The total the store page carries in the __NEXT_DATA__ block, the state Next.js sends along with the HTML."""
    block = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not block:
        return None
    state = json.loads(block.group(1))
    data = json.loads(state["props"]["pageProps"]["data"])  # a JSON stored inside a string
    return data["catalogServer"]["meta"]["totalItemsCount"]


def record(row, target=CHECK_LOG):
    """Writes the check to dados/conferencia.csv, one row per day. Checking the same day again replaces its row."""
    rows = []
    if target.exists():
        with target.open(encoding="utf-8", newline="") as file:
            rows = [old for old in csv.DictReader(file) if old["dia"] != row["dia"]]
    rows.append(row)
    with target.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda item: item["dia"]))


def verify(folder=None):
    folder = folder or day_folder()
    products = read_day(folder)
    ids = Counter(product["id"] for product in products)
    repeated = {product_id: times for product_id, times in ids.items() if times > 1}
    declared = declared_total(folder)
    log.info("collection: %s products read, %s unique; the API declares %s", len(products), len(ids), declared)
    log.info("repeated across pages: %s", ", ".join(f"{i} ({n} times)" for i, n in repeated.items()) or "none")
    html = store_page(folder)
    store = page_total(html) if html else None
    log.info("the store page shows %s products", store)
    coverage = len(ids) / declared
    log.info("coverage: %s of %s, %.1f%%; %s missing", len(ids), declared, coverage * 100, declared - len(ids))
    record({"dia": Path(folder).name, "lidos": len(products), "diferentes": len(ids), "repetidos": len(repeated),
            "declarado": declared, "loja": store, "cobertura": f"{coverage:.3f}"})
    if coverage < MIN_COVERAGE:
        raise SystemExit(f"Coverage was {coverage * 100:.1f}%, below {MIN_COVERAGE * 100:.0f}%. Check the repeated products before moving on.")
    return len(ids)


if __name__ == "__main__":
    verify()
