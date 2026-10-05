-- Staging and enriched tables for bank agency reviews

CREATE TABLE IF NOT EXISTS bank_reviews_staging (
    place_id TEXT,
    bank_name TEXT,
    branch_name TEXT,
    region TEXT,
    address TEXT,
    branch_rating REAL,
    user_rating_count INTEGER,
    review_text TEXT,
    review_rating INTEGER,
    person_id TEXT,
    review_time TIMESTAMP,
    PRIMARY KEY (place_id, person_id, review_time)
);

CREATE TABLE IF NOT EXISTS bank_reviews_enriched (
    place_id TEXT,
    bank_name TEXT,
    branch_name TEXT,
    region TEXT,
    address TEXT,
    branch_rating REAL,
    user_rating_count INTEGER,
    review_text TEXT,
    review_rating INTEGER,
    person_id TEXT,
    review_time TIMESTAMP,
    language TEXT,
    sentiment TEXT,
    topic TEXT,
    PRIMARY KEY (place_id, person_id, review_time)
);
