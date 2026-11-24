"""Requests the graphics cards from Kabum's catalog API, the same one the category page uses, page by page.

Each response goes to disk as it came, in a folder named after the collection day. What is already saved today is not requested again."""

import json
import logging
import os
import time
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

USER_AGENT = os.getenv("KABUM_USER_AGENT")
if not USER_AGENT:
    raise SystemExit("KABUM_USER_AGENT is missing from the .env file. Copy .env.example to .env and fill it in.")

API = "https://servicespub.prod.api.aws.grupokabum.com.br"
CATEGORY = "/catalog/v2/products-by-category/hardware/placa-de-video-vga"
PAGE_SIZE = 120  # products per page, the maximum the API accepts; the same on every request
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}
WAIT = 3.0  # seconds to wait after each request
MAX_PAGES = 20  # a ceiling: the category had 4 pages on 2026-11-14

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("kabum")


def day_folder(day=None):
    """dados/bronze/2026-11-14/: one folder per collection day."""
    return Path("dados/bronze") / f"{day or date.today()}"


def fetch(path):
    """Requests an API path and returns the response bytes. Stops on any response that is not JSON with status 200."""
    response = httpx.get(API + path, headers=HEADERS, timeout=30)
    time.sleep(WAIT)
    content_type = response.headers.get("content-type", "")
    if response.status_code != 200 or "json" not in content_type:
        # 403, 429 or an HTML challenge page instead of JSON: the site said no. The program stops here.
        Path("dados").mkdir(exist_ok=True)
        Path("dados/ultima_recusa.html").write_bytes(response.content)
        raise SystemExit(f"{path} answered {response.status_code} ({content_type}). The response is in dados/ultima_recusa.html. Stop and read it.")
    return response.content


def collect_page(number, path, folder):
    """Returns the page JSON, from disk if it was already downloaded today, or by requesting it from the API."""
    target = folder / f"pagina-{number:03d}.json"
    if target.exists():
        log.info("already have %s, not requesting it again", target)
        return json.loads(target.read_text(encoding="utf-8"))
    content = fetch(path)
    folder.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    log.info("downloaded page %s: %s bytes into %s", number, len(content), target)
    return json.loads(content)


def page_path(number):
    """The page path, always with the same page size."""
    return f"{CATEGORY}?page_number={number}&page_size={PAGE_SIZE}"


def collect(folder=None):
    """Requests page 1, reads how many pages the category has and requests the others, one at a time.

    The API's links.next is not followed: in the 2026-11-14 run it changed the page size midway,
    and the following pages repeated products already downloaded (saidas/armadilha-links-next.txt)."""
    folder = folder or day_folder()
    first = collect_page(1, page_path(1), folder)
    total_pages = first["meta"]["total_pages_count"]
    if total_pages > MAX_PAGES:
        raise SystemExit(f"The category claims {total_pages} pages, above the ceiling of {MAX_PAGES}. Check before moving on.")
    for number in range(2, total_pages + 1):
        collect_page(number, page_path(number), folder)
    log.info("day's collection: %s pages in %s", total_pages, folder)
    return total_pages


if __name__ == "__main__":
    collect()
