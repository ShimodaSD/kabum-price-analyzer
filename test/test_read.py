"""Tests for reading one API page. The sample was written by hand, with the structure of the real response."""

from pathlib import Path

from read import read_page

SAMPLE = Path(__file__).parent / "page_sample.json"


def test_one_dictionary_per_product_with_fields_as_received():
    products = read_page(SAMPLE.read_bytes())
    assert len(products) == 2
    assert products[0]["id"] == 111
    assert products[0]["price_with_discount"] == 950.0
    assert products[0]["fabricante"] == "Fabricante A"


def test_offer_price_comes_from_offer_block():
    products = read_page(SAMPLE.read_bytes())
    assert products[0]["oferta_price_with_discount"] == 855.0
    assert products[0]["oferta_ends_at"] == 1795701540
    assert products[1]["oferta_price_with_discount"] is None


def test_product_without_manufacturer_has_empty_field():
    products = read_page(SAMPLE.read_bytes())
    assert products[1]["fabricante"] is None
    assert products[1]["available"] is False
