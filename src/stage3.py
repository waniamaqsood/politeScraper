import json
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

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "output"


def get_detail_cache_path(product_url):

    book_name = product_url.rstrip("/").split("/")[-2]

    return CACHE_DIR / f"{book_name}.html"


def fetch_book_page(product_url, cache_path):

    if cache_path.exists():
        print(f"Using cached page: {cache_path}")

        html = cache_path.read_text(
            encoding="utf-8"
        )

        return html, "cache"

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

    except requests.Timeout as error:
        print(f"Request timed out: {error}")

        time.sleep(REQUEST_DELAY)

        try:
            response = requests.get(
                product_url,
                headers=headers,
                timeout=TIMEOUT
            )
        except requests.RequestException as error:
            print(f"Retry failed: {error}")
            return None, "failed"

    except requests.RequestException as error:
        print(f"Request failed: {error}")
        return None, "failed"

    print(f"Status code: {response.status_code}")

    if response.status_code == 200:
        print("Fetch Successful!")

    elif response.status_code in (403, 404):
        print("Denied! Fetch won't try again")
        return None, "failed"

    elif 500 <= response.status_code < 600:

        print("Server error! Retrying once...")

        time.sleep(REQUEST_DELAY)

        try:
            response = requests.get(
                product_url,
                headers=headers,
                timeout=TIMEOUT
            )
        except requests.RequestException as error:
            print(f"Retry failed: {error}")
            return None, "failed"

        print(f"Retry status code: {response.status_code}")

        if response.status_code != 200:
            print("Retry failed")
            return None, "failed"

        print("Retry successful!")

    else:
        print("Fetch failed")
        return None, "failed"

    response.encoding = "utf-8"

    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    cache_path.write_text(
        response.text,
        encoding="utf-8"
    )

    return response.text, "fetched"


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

    start_time = datetime.now(timezone.utc)
    start_timestamp = start_time.isoformat()

    start_counter = time.perf_counter()

    book_sources = discover_books()

    book_sources[
        "https://books.toscrape.com/catalogue/fake-book-999999/"
    ] = "fake-test"

    all_details = []

    pages_fetched = 0
    cache_hits = 0
    valid_records = 0
    invalid_records = 0
    failed_pages = []

    for product_url, source_page in book_sources.items():

        print("\nProcessing book:")
        print(product_url)

        cache_path = get_detail_cache_path(
            product_url
        )

        html, fetch_status = fetch_book_page(
            product_url,
            cache_path
        )

        if fetch_status == "cache":
            cache_hits += 1

        elif fetch_status == "fetched":
            pages_fetched += 1

        elif fetch_status == "failed":
            failed_pages.append(product_url)
            continue

        detail = parse_book_details(
            html,
            product_url,
            source_page
        )

        if detail is not None:
            all_details.append(detail)
            valid_records += 1
        else:
            invalid_records += 1

    duration = time.perf_counter() - start_counter

    report = {
        "start_time": start_timestamp,
        "duration_seconds": round(duration, 2),
        "pages_fetched": pages_fetched,
        "cache_hits": cache_hits,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "failed_pages": len(failed_pages)
    }

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    report_path = OUTPUT_DIR / "run-report.json"

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n--- Run Report ---")
    print(json.dumps(report, indent=4))

    print("\n--- Checkpoint ---")
    print(f"detail_pages={len(all_details)}")

    if all_details:
        print("\n--- Complete raw record ---")
        print(all_details[0])

    run_stats = {
    "pages_fetched": pages_fetched,
    "cache_hits": cache_hits,
    "failed_pages": failed_pages
}

    return all_details, run_stats


if __name__ == "__main__":
    main()
