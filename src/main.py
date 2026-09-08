from pathlib import Path
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"
USER_AGENT = (
    "FlyRankInternship/1.0 "
    "(+https://github.com/waniamaqsood/politeScraper.git)"
)
TIMEOUT = 5
REQUEST_DELAY = 0.5

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"


def get_cache_path(page_number):
    return CACHE_DIR / f"catalogue-page-{page_number}.html"


def fetch_and_cache(page_url, cache_path):
    """
    Fetch a catalogue page from the website and save it to the cache.
    """

    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(
            page_url,
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

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(response.text, encoding="utf-8")

    print(f"Saved page to {cache_path}")

    return response.text


def load_page(page_url, cache_path):
    """
    Load a page from cache if it exists.
    Otherwise fetch it from the website and cache it.
    """

    if cache_path.exists():
        print(f"Using cached page: {cache_path}")
        return cache_path.read_text(encoding="utf-8")

    # This is a real request, so wait before making it.
    time.sleep(REQUEST_DELAY)

    return fetch_and_cache(page_url, cache_path)


def parse_content(html, page_url):
    """
    Extract book URLs and the next catalogue page URL.
    """

    soup = BeautifulSoup(html, "html.parser")

    book_urls = set()

    # Extract every book link on this catalogue page.
    for link in soup.select("article.product_pod h3 a"):
        href = link.get("href")

        if href:
            absolute_url = urljoin(page_url, href)
            book_urls.add(absolute_url)

    # Find the catalogue's own "next" link.
    next_link = soup.select_one("li.next a")

    if next_link:
        next_href = next_link.get("href")
        next_url = urljoin(page_url, next_href)
    else:
        next_url = None

    return book_urls, next_url


def main():
    current_url = BASE_URL
    all_book_urls = set()

    catalogue_pages = 0

    while catalogue_pages < 3:
        catalogue_pages += 1

        cache_path = get_cache_path(catalogue_pages)

        print(f"\nProcessing catalogue page {catalogue_pages}")
        print(f"URL: {current_url}")

        html = load_page(current_url, cache_path)

        if html is None:
            print("Could not load page. Stopping.")
            break

        book_urls, next_url = parse_content(
            html,
            current_url
        )

        print(f"Books found on this page: {len(book_urls)}")

        all_book_urls.update(book_urls)

        # Stop after page 3.
        if catalogue_pages == 3:
            break

        # Follow the catalogue's own next link.
        if next_url is None:
            print("No next page found. Stopping.")
            break

        current_url = next_url

    print("\n--- Checkpoint ---")
    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={len(all_book_urls)}")
    print(f"unique_urls={len(all_book_urls)}")


if __name__ == "__main__":
    main()