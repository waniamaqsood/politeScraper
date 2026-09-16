# Polite Scraper

A small, polite web scraper built as part of the FlyRank Backend Track internship.

The project discovers and extracts book records from **Books to Scrape**, a sandbox website intended for scraping practice.

## Target Classification

**Target:** Books to Scrape
**URL:** https://books.toscrape.com/

Books to Scrape is a practice/sandbox website for web scraping. This project uses it to demonstrate catalogue discovery, detail-page extraction, caching, validation, and structured JSON output.

> I will not reuse this code on another site without checking its rules and terms first.

## How to Run

From the project root:

```powershell
cd src
python stage4.py
```

Stage 4 runs the pipeline by calling the earlier stages, so this single command performs the complete scraping and validation workflow.

The final outputs are written to:

```text
output/books.json
output/errors.json
```

## Lane

**Backend / Python**

The scraper is implemented in Python and uses:

* `requests` — HTTP requests
* `BeautifulSoup` — HTML parsing
* `Pydantic` — record schema and validation
* `json` — structured output
* Python standard library — caching, timestamps, paths, and other utilities

### Installation

Create and activate a Python environment if desired, then install the project dependencies:

```powershell
pip install requests beautifulsoup4 pydantic
```

No database or external service is required.

## Pipeline

The scraper is divided into stages:

1. **Stage 1 — Fetch and cache**

   * Fetches the catalogue page.
   * Saves the HTML locally so it can be reused.

2. **Stage 2 — Discover**

   * Follows the catalogue's `next` links.
   * Processes the first three catalogue pages.
   * Discovers 60 unique book URLs.
   * Uses absolute URLs for product identity.

3. **Stage 3 — Extract**

   * Opens each book detail page.
   * Extracts the raw book fields.
   * Preserves the original price text.
   * Records the source catalogue page and fetch timestamp.

4. **Stage 4 — Validate and normalize**

   * Converts `price_text` into numeric `price_gbp`.
   * Validates records with Pydantic.
   * Deduplicates records using `product_url`.
   * Writes valid records to `books.json`.
   * Sends invalid records and their validation errors to `errors.json`.

## Record Schema

Each finished book record contains:

| Field               | Type           | Description                                  |
| ------------------- | -------------- | -------------------------------------------- |
| `title`             | string         | Book title                                   |
| `product_url`       | string         | Absolute canonical product URL               |
| `price_text`        | string         | Original price as scraped                    |
| `price_gbp`         | float          | Numeric price in GBP                         |
| `availability_text` | string         | Original availability text                   |
| `rating_text`       | string         | Star rating text                             |
| `description`       | string or null | Book description when available              |
| `source_page`       | string         | Catalogue page where the book was discovered |
| `fetched_at`        | string         | UTC timestamp for the extracted record       |

Example:

```json
{
    "title": "A Light in the Attic",
    "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    "price_text": "£51.77",
    "price_gbp": 51.77,
    "availability_text": "In stock (22 available)",
    "rating_text": "Three",
    "description": "...",
    "source_page": "https://books.toscrape.com/catalogue/page-1.html",
    "fetched_at": "2026-09-11T06:09:26.348825+00:00"
}
```

## Politeness Rules

The scraper follows the same basic politeness rules throughout the fetching stages:

### User-Agent

Requests identify the scraper with a descriptive User-Agent:

```text
FlyRankInternshipA9/1.0 (+https://github.com/waniamaqsood/politeScraper.git)
```

### Delay

A **0.5 second delay** is used before real HTTP requests.

Cached pages do not require another network request or delay.

### Timeout

HTTP requests use a **5 second timeout** so the scraper does not wait indefinitely for a response.

### Cache

Fetched HTML pages are stored locally in the `cache/` directory.

When a page is already cached, the scraper reuses the cached copy instead of making another request.

This reduces unnecessary requests to the target site and also makes development and reruns faster.

## Output

After a successful run:

```text
output/
├── books.json
└── errors.json
```

`books.json` contains the validated records.

`errors.json` contains records that fail validation together with the reason for failure.

The scraper uses the absolute `product_url` as the record identity, so duplicate URLs are counted only once.

## Checkpoint

The completed pipeline discovers and processes:

```text
catalogue_pages=3
discovered=60
unique_urls=60
detail_pages=60
valid_records=60
invalid_records=0
```

## Limitation

This scraper is intentionally built for the current structure of **Books to Scrape**. Its HTML selectors depend on the site's existing page structure, so a significant change to the site's HTML could cause fields to stop being extracted correctly or require selector updates.
