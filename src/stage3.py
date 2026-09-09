import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from stage2 import main as discover_books


USER_AGENT = (
    "FlyRankInternshipA9/1.0 "
    "(+https://github.com/waniamaqsood/politeScraper.git)"
)

TIMEOUT = 5
REQUEST_DELAY = 0.5

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"


def get_detail_cache_path(product_url):

    book_name = product_url.rstrip("/").split("/")[-2]

    return CACHE_DIR / f"{book_name}.html"


def fetch_book_page(product_url, cache_path):

    if cache_path.exists():
        print(f"Using cached page: {cache_path}")

        return cache_path.read_text(
            encoding="utf-8"
        )

    time.sleep(REQUEST_DELAY)

    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(
            product_url,
            headers=headers,
            timeout=TIMEOUT
        )
    except requests.RequestException as error:
        print(f"Request failed: {error}")
        return None

    print(f"Status code: {response.status_code}")

    if response.status_code != 200:
        print("Fetch failed, HTML will not be processed")
        return None

    response.encoding = "utf-8"

    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    cache_path.write_text(
        response.text,
        encoding="utf-8"
    )

    return response.text


def parse_book_details(
    html,
    product_url,
    source_page
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    product = soup.select_one(".product_page")

    if product is None:
        return None

    title = product.select_one("h1")

    price = product.select_one(".price_color")

    availability = product.select_one(".availability")

    rating = product.select_one(".star-rating")

    description_heading = soup.select_one(
        "#product_description"
    )

    if description_heading:
        description_element = (
            description_heading.find_next_sibling("p")
        )
    else:
        description_element = None

    fetched_at = datetime.now(
        timezone.utc
    ).isoformat()

    detail = {
        "title": title.get_text(strip=True)
        if title else None,

        "product_url": product_url,

        "price_text": price.get_text(strip=True)
        if price else None,

        "availability_text": availability.get_text(
            " ",
            strip=True
        ) if availability else None,

        "rating_text": rating.get("class")[1]
        if rating and len(rating.get("class")) > 1
        else None,

        "description": description_element.get_text(
            " ",
            strip=True
        ) if description_element else None,

        "source_page": source_page,

        "fetched_at": fetched_at
    }

    return detail


def main():

    # Get the 60 URLs and their catalogue pages
    book_sources = discover_books()

    all_details = []

    for product_url, source_page in book_sources.items():

        print("\nProcessing book:")
        print(product_url)

        cache_path = get_detail_cache_path(
            product_url
        )

        html = fetch_book_page(
            product_url,
            cache_path
        )

        if html is None:
            continue

        detail = parse_book_details(
            html,
            product_url,
            source_page
        )

        if detail is not None:
            all_details.append(detail)

    print("\n--- Checkpoint ---")

    print(f"detail_pages={len(all_details)}")

    if all_details:
        print("\n--- Complete raw record ---")
        print(all_details[0])


if __name__ == "__main__":
    main()