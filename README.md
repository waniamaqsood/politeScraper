# Books Scraper Pipeline

A Python pipeline that collects structured records for **60 books** from [Books to Scrape](https://books.toscrape.com/) (a sandbox site built for scraping practice), validates them, and writes clean JSON plus a run report. Built for the FlyRank Internship Backend Track, Week 5 (The Polite Scraper).

It is treated as a small data-ingestion job rather than a one-off script: fetching, caching, pagination, extraction, validation, retry rules and run reporting are separate concerns.

## What it does

1. **Discovers** books by following the catalogue's `next` links for the first **3 pages**, yielding 60 unique, absolute product URLs.
2. **Fetches** each detail page politely and caches the HTML in `cache/`.
3. **Extracts** title, product URL, price text, availability, star rating, description, source catalogue page and fetch timestamp.
4. **Normalizes and validates**: converts `£51.77` to `price_gbp = 51.77` (raw text preserved) and validates every record with Pydantic.
5. **Writes** `output/books.json` (valid), `output/errors.json` (invalid, with reasons) and `output/run-report.json`.

## Data flow

```text
catalogue pages 1–3 ──▶ 60 product URLs ──▶ fetch detail page ──▶ parse HTML ──▶ add price_gbp
        (cache/)                              (cache/ first)                          │
                                                                                      ▼
                          output/run-report.json ◀── counts ◀── Pydantic validation ──┬─▶ output/books.json
                                                                                       └─▶ output/errors.json
```

**Stack:** Python · `requests` · BeautifulSoup · Pydantic.

## Run it

```bash
pip install requests beautifulsoup4 pydantic
cd src
python stage4.py          # runs the whole pipeline (stage4 calls stage3, which calls stage2)
```

Outputs go to `output/`. Delete `cache/` to force a fresh crawl.

### Sample record

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "…",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-09-11T06:09:26.348825+00:00"
}
```

### Run report

```json
{
  "start_time": "…",
  "duration_seconds": 0.41,
  "pages_fetched": 0,
  "cache_hits": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

This is a cached run (60 hits, 0 network fetches). A cold run fetches pages and takes longer because of the delay.

## Responsible scraping

- **Target:** a sandbox site intended for scraping practice. At the start of the project (Sep 8, 2026) `https://books.toscrape.com/robots.txt` returned **404** (no robots file). The code does not fetch or parse `robots.txt` itself; re-check the rules before pointing this at any other site.
- **User-Agent:** `FlyRankInternshipA9/1.0 (+https://github.com/waniamaqsood/books-scraper-pipeline)`: identifies the scraper and where to find it.
- **Delay:** 0.5 s before every real network request (cached pages skip it).
- **Timeout:** 5 s per request.
- **Cache:** every fetched page is stored and reused on reruns, so reruns don't hit the site. The cache **never expires**.

## Reliability

Detail-page fetching behaves as follows (checked with mocked HTTP responses):

| Situation | Behavior |
|---|---|
| 200 | Cache and parse |
| 403 / 404 | **No retry**; page recorded as failed |
| 5xx | Retry **once**, then record as failed |
| Timeout | Retry **once**, then record as failed |
| Other connection errors | No retry; page recorded as failed |

A failed page is counted in `failed_pages` and the run continues. Records that fail Pydantic validation go to `errors.json` with the validation errors rather than stopping the run.

**Reruns:** the same set of 60 valid records is produced each time from the cache. Record **order** and each record's `fetched_at` timestamp vary between runs, so the output files are not byte-identical.

## Implementation decisions

- Absolute `product_url` is the record identity, used for de-duplication.
- Raw values (`price_text`, `availability_text`, `rating_text`) are kept next to normalized ones.
- Pydantic gives a precise, machine-readable error per failed field.
- A run report (pages fetched, cache hits, valid/invalid counts, failed pages, duration) makes each run observable.

## Limitations

- **Selectors are tied to this site's HTML**; a layout change would break extraction.
- **A malformed price text (e.g. `N/A`) raises `ValueError` and stops the run** instead of landing in `errors.json`. Price conversion needs a guard.
- **Catalogue pages have no retry**; a failed catalogue fetch ends discovery.
- **`fetched_at` is set when the page is parsed**, not when it was downloaded, so cached pages get a fresh timestamp each run.
- Stages are numbered scripts chained by import (`stage1.py` is unused) with shared constants repeated across files. They should become named modules with one config.
- **No automated tests.** The cached HTML in `cache/` is ready to serve as test fixtures.
- Single-threaded by design (politeness), so a cold run is slow.
