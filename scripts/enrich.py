"""Enrich staged reviews with language detection, BERT sentiment, and topic labels."""

import os
import re
from pathlib import Path
from typing import Optional

import psycopg2
from dotenv import load_dotenv
from langdetect import DetectorFactory, detect
from psycopg2.extras import execute_batch
from transformers import pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
DetectorFactory.seed = 0

TOPICS = [
    "security",
    "customer service",
    "staff behavior",
    "account management",
    "ATM issues",
    "mobile banking",
    "billing",
    "wait times",
    "loans",
    "other",
]

sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
)
topic_classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli",
)


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


def clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub("", text)
    text = " ".join(text.split())
    return text.strip() or None


def detect_language(text: Optional[str]) -> Optional[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return None
    try:
        return detect(cleaned)
    except Exception:
        return "unknown"


def get_sentiment(text: Optional[str]) -> Optional[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return None
    try:
        result = sentiment_analyzer(cleaned[:512])
        score = float(result[0]["label"].split()[0])
        if score > 3:
            return "positive"
        if score < 3:
            return "negative"
        return "neutral"
    except Exception as exc:
        print(f"Sentiment error: {exc}")
        return None


def get_topic(text: Optional[str]) -> Optional[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return None
    try:
        result = topic_classifier(
            cleaned[:512],
            TOPICS,
            multi_label=False,
            hypothesis_template="This text is about {}.",
        )
        if result["scores"][0] < 0.3:
            return "other"
        return result["labels"][0]
    except Exception as exc:
        print(f"Topic error: {exc}")
        return None


def main():
    conn = get_connection()
    cur = conn.cursor()

    with open(PROJECT_ROOT / "sql" / "create_staging.sql", encoding="utf-8") as file:
        cur.execute(file.read())

    cur.execute(
        """
        SELECT place_id, bank_name, branch_name, region, address, branch_rating,
               user_rating_count, review_text, review_rating, person_id, review_time
        FROM bank_reviews_staging
        """
    )
    rows = cur.fetchall()
    print(f"Enriching {len(rows)} staged reviews")

    enriched = []
    for idx, row in enumerate(rows, start=1):
        review_text = row[7]
        language = detect_language(review_text)
        sentiment = get_sentiment(review_text)
        topic = get_topic(review_text)
        enriched.append(row + (language, sentiment, topic))
        if idx % 100 == 0:
            print(f"Processed {idx}/{len(rows)}")

    cur.execute("TRUNCATE TABLE bank_reviews_enriched")
    insert_sql = """
        INSERT INTO bank_reviews_enriched (
            place_id, bank_name, branch_name, region, address, branch_rating,
            user_rating_count, review_text, review_rating, person_id, review_time,
            language, sentiment, topic
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_batch(cur, insert_sql, enriched, page_size=200)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {len(enriched)} rows into bank_reviews_enriched")


if __name__ == "__main__":
    main()
