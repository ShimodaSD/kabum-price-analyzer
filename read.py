"""Reads the saved pages and returns one dictionary per product, with the fields as the API sent them."""

import json
import sys
from pathlib import Path

FIELDS = ["id", "title", "price", "price_with_discount", "old_price", "discount_percentage",
          "oferta_price", "oferta_price_with_discount", "oferta_ends_at", "available", "stock", "fabricante", "product_link"]


def read_page(content):
    """Takes the JSON of one page and returns its products."""
    response = json.loads(content)
    products = []
    for item in response["data"]:
        attributes = item["attributes"]
        offer = attributes.get("offer") or {}  # only products on offer have this block; the big price on the card comes from it
        products.append({
            "id": item["id"],
            "title": attributes.get("title"),
            "price": attributes.get("price"),
            "price_with_discount": attributes.get("price_with_discount"),
            "old_price": attributes.get("old_price"),
            "discount_percentage": attributes.get("discount_percentage"),
            "oferta_price": offer.get("price"),
            "oferta_price_with_discount": offer.get("price_with_discount"),
            "oferta_ends_at": offer.get("ends_at"),
            "available": attributes.get("available"),
            "stock": attributes.get("stock"),
            "fabricante": (attributes.get("manufacturer") or {}).get("name"),
            "product_link": attributes.get("product_link"),
        })
    return products


def read_day(folder):
    """All products from one collection day, in page order."""
    products = []
    for file in sorted(Path(folder).glob("pagina-*.json")):
        products += read_page(file.read_bytes())
    return products


if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder = Path(sys.argv[1])
    else:
        days = sorted(Path("dados/bronze").glob("*"))  # empty if the folder does not exist yet
        if not days:
            raise SystemExit("No collection in dados/bronze yet. Run first: uv run python collect.py")
        folder = days[-1]
    products = read_day(folder)
    print(f"{folder}: {len(products)} products")
    for field, value in products[0].items():
        print(f"  {field}: {value}")
