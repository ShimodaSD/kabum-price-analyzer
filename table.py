"""Builds the price history: one row per product per collection day, with the values as the API sent them."""

import csv
from pathlib import Path

from collect import log
from read import FIELDS, read_day

CSV = Path("dados/precos.csv")
COLUMNS = ["dia", *FIELDS]


def build(bronze=Path("dados/bronze")):
    """One row per product per collection day, from the bronze day folders."""
    rows = []
    for folder in sorted(bronze.iterdir()):
        if not folder.is_dir():
            continue
        seen = set()
        for product in read_day(folder):
            if product["id"] in seen:  # the same product in two pages of the same day goes in once
                continue
            seen.add(product["id"])
            rows.append({"dia": folder.name, **product})
    return rows


def write_csv(rows, target=CSV):
    with target.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    days = sorted({row["dia"] for row in rows})
    log.info("wrote %s rows to %s, from %s day(s): %s", len(rows), target, len(days), ", ".join(days))


if __name__ == "__main__":
    write_csv(build())
