from pathlib import Path
import requests


BASE_URL = "https://books.toscrape.com/"

USER_AGENT = (
    "FlyRankInternshipA9/1.0 "
    "(+https://github.com/waniamaqsood/politeScraper.git)"
)

TIMEOUT = 5

CACHE_PATH = Path(__file__).resolve().parent.parent / "cache" / "catalogue-page-1.html"


def fetch_and_cache():
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(
            BASE_URL,
            headers=headers,
            timeout=TIMEOUT
        )
    except requests.RequestException as error:
        print(f"Request failed: {error}")
        return

    print(f"Status code: {response.status_code}")

    if response.status_code != 200:
        print("Fetch failed, HTML will not be processed")
        return

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(response.text, encoding="utf-8")

    print(f"Saved page to {CACHE_PATH}")


if __name__ == "__main__":
    fetch_and_cache()