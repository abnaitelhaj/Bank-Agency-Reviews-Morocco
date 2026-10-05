"""Flatten raw Places JSON into CSV and load a PostgreSQL staging table."""

import csv
import json
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_batch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

RAW_JSON = PROJECT_ROOT / "data" / "raw" / "data-of-banks.json"
STAGING_CSV = PROJECT_ROOT / "data" / "staging" / "bank_reviews_staging.csv"
CREATE_SQL = PROJECT_ROOT / "sql" / "create_staging.sql"
CLEANING_SQL = PROJECT_ROOT / "sql" / "cleaning.sql"

COLUMNS = [
    "place_id",
    "bank_name",
    "branch_name",
    "region",
    "address",
    "branch_rating",
    "user_rating_count",
    "review_text",
    "review_rating",
    "person_id",
    "review_time",
]


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


def flatten_reviews(raw_path=RAW_JSON):
    with open(raw_path, encoding="utf-8") as file:
        places = json.load(file)

    rows = []
    for place in places:
        place_id = place.get("id")
        bank_name = place.get("bank_name")
        display_name = (place.get("displayName") or {}).get("text")
        short_address = place.get("shortFormattedAddress")
        branch_name = f"{display_name} {short_address}".strip() if display_name else short_address
        region = place.get("region")
        address = place.get("formattedAddress")
        branch_rating = place.get("rating")
        user_rating_count = place.get("userRatingCount") or 0

        for review in place.get("reviews") or []:
            text_obj = review.get("text") or {}
            review_text = text_obj.get("text") if isinstance(text_obj, dict) else text_obj
            person_id = (review.get("authorAttribution") or {}).get("displayName")
            review_time = review.get("publishTime")
            if not person_id or not review_time:
                continue

            rows.append(
                {
                    "place_id": place_id,
                    "bank_name": bank_name,
                    "branch_name": branch_name,
                    "region": region,
                    "address": address,
                    "branch_rating": branch_rating,
                    "user_rating_count": user_rating_count,
                    "review_text": review_text,
                    "review_rating": review.get("rating"),
                    "person_id": person_id,
                    "review_time": review_time,
                }
            )
    return rows


def write_csv(rows, csv_path=STAGING_CSV):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} staging rows to {csv_path}")


def load_staging(rows):
    conn = get_connection()
    cur = conn.cursor()

    with open(CREATE_SQL, encoding="utf-8") as file:
        cur.execute(file.read())

    cur.execute("TRUNCATE TABLE bank_reviews_staging")

    insert_sql = f"""
        INSERT INTO bank_reviews_staging ({', '.join(COLUMNS)})
        VALUES ({', '.join(['%s'] * len(COLUMNS))})
        ON CONFLICT (place_id, person_id, review_time) DO UPDATE SET
            bank_name = EXCLUDED.bank_name,
            branch_name = EXCLUDED.branch_name,
            region = EXCLUDED.region,
            address = EXCLUDED.address,
            branch_rating = EXCLUDED.branch_rating,
            user_rating_count = EXCLUDED.user_rating_count,
            review_text = EXCLUDED.review_text,
            review_rating = EXCLUDED.review_rating
    """
    values = [tuple(row[col] for col in COLUMNS) for row in rows]
    execute_batch(cur, insert_sql, values, page_size=500)

    with open(CLEANING_SQL, encoding="utf-8") as file:
        cur.execute(file.read())

    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {len(rows)} rows into bank_reviews_staging")


def main():
    rows = flatten_reviews()
    write_csv(rows)
    load_staging(rows)


if __name__ == "__main__":
    main()
