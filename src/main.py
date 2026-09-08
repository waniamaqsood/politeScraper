from pathlib import Path
import requests

url = "https://books.toscrape.com/"
userAgent = "FlyRankInternship/1.0 (+https://github.com/waniamaqsood/politeScraper.git)"
timeout = 5

CACHE_PATH = Path(__file__).resolve().parent.parent / "cache" / "catalogue-page-1.html"


def fetchAndCache():
    headers = {
        "User-Agent": userAgent
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout
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
    fetchAndCache()