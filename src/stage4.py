from typing import Any, Optional
from pathlib import Path
import json
from pydantic import BaseModel, ValidationError
from stage3 import main as get_all_details

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


def convert_text_nums(all_details: list[dict[str, Any]]):
    for book in all_details:
        price_as_text = book["price_text"]
        only_price = price_as_text.replace("£", "").replace("Â", "").strip()
        price_as_float = float(only_price)
        book["price_gbp"] = price_as_float
    return all_details

def validate_records(
    all_details: list[dict[str, Any]]
):

    valid_records = []
    errors = []
    seen_urls = set()

    for book in all_details:
        product_url = book.get("product_url")
        if product_url in seen_urls:
            continue
        seen_urls.add(product_url)

        try:
            validated_book = BookRecord.model_validate(book)
            valid_records.append(
                validated_book.model_dump()
            )

        except ValidationError as error:
            errors.append(
                {
                    "record": book,
                    "reason": str(error)
                }
            )

    return valid_records, errors


def write_output(
    valid_records,
    errors
):

    output_dir = Path(__file__).resolve().parent.parent / "output"
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    books_path = output_dir / "books.json"
    errors_path = output_dir / "errors.json"

    with open(
        books_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            valid_records,
            f,
            indent=4,
            ensure_ascii=False
        )

    with open(
        errors_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            errors,
            f,
            indent=4,
            ensure_ascii=False
        )


def main():

    all_details = get_all_details()
    all_details = convert_text_nums(all_details)
    valid_records, errors = validate_records(all_details)
    write_output(valid_records, errors)

    print("\n--- Checkpoint ---")
    print(f"input_records={len(all_details)}")
    print(f"valid_records={len(valid_records)}")
    print(f"errors={len(errors)}")

    print("\nOutput written to:")
    print("output/books.json")
    print("output/errors.json")


if __name__ == "__main__":
    main()