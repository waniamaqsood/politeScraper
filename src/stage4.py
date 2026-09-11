import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ValidationError

from stage3 import main as get_all_details


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"


class BookRecord(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: Optional[str]
    source_page: str
    fetched_at: str


def convert_text_nums(
    all_details: list[dict[str, Any]]
) -> list[dict[str, Any]]:

    converted_records = []

    for detail in all_details:

        price_text = detail.get("price_text")

        if price_text:
            price_gbp = float(
                price_text.replace("£", "").strip()
            )
        else:
            price_gbp = None

        detail["price_gbp"] = price_gbp

        converted_records.append(detail)

    return converted_records


def validate_records(
    all_details: list[dict[str, Any]]
):

    valid_records = []
    errors = []

    for detail in all_details:

        try:
            record = BookRecord.model_validate(detail)

            valid_records.append(
                record.model_dump()
            )

        except ValidationError as error:

            errors.append({
                "product_url": detail.get("product_url"),
                "errors": error.errors()
            })

    return valid_records, errors


def write_output(
    valid_records,
    errors
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    books_path = OUTPUT_DIR / "books.json"

    with open(
        books_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            valid_records,
            file,
            indent=4,
            ensure_ascii=False
        )

    errors_path = OUTPUT_DIR / "errors.json"

    with open(
        errors_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            errors,
            file,
            indent=4,
            ensure_ascii=False
        )


def write_run_report(
    run_stats,
    valid_records,
    errors,
    start_timestamp,
    duration
):

    report = {
        "start_time": start_timestamp,
        "duration_seconds": round(
            duration,
            2
        ),
        "pages_fetched": run_stats[
            "pages_fetched"
        ],
        "cache_hits": run_stats[
            "cache_hits"
        ],
        "valid_records": len(
            valid_records
        ),
        "invalid_records": len(
            errors
        ),
        "failed_pages": len(
            run_stats["failed_pages"]
        )
    }

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

    return report


def main():

    start_time = datetime.now(
        timezone.utc
    )

    start_timestamp = start_time.isoformat()

    start_counter = time.perf_counter()

    # Stage 3 performs the scraping.
    # It returns both the scraped records
    # and the fetch statistics.
    all_details, run_stats = get_all_details()

    # Convert text values such as "£50.10"
    # into the numeric price_gbp field.
    all_details = convert_text_nums(
        all_details
    )

    # Validate every scraped record.
    valid_records, errors = validate_records(
        all_details
    )

    # Write books.json and errors.json.
    write_output(
        valid_records,
        errors
    )

    duration = (
        time.perf_counter()
        - start_counter
    )

    # Write the final Stage 5 run report.
    report = write_run_report(
        run_stats=run_stats,
        valid_records=valid_records,
        errors=errors,
        start_timestamp=start_timestamp,
        duration=duration
    )

    print("\n--- Validation Checkpoint ---")

    print(
        f"valid_records={len(valid_records)}"
    )

    print(
        f"invalid_records={len(errors)}"
    )

    print(
        f"failed_pages="
        f"{len(run_stats['failed_pages'])}"
    )

    print("\n--- Run Report ---")

    print(
        json.dumps(
            report,
            indent=4
        )
    )

    print("\nOutput files written:")

    print(
        OUTPUT_DIR / "books.json"
    )

    print(
        OUTPUT_DIR / "errors.json"
    )

    print(
        OUTPUT_DIR / "run-report.json"
    )

    return valid_records, errors


if __name__ == "__main__":
    main()
