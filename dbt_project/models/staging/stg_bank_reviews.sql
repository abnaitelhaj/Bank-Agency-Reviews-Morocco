{{
    config(materialized='view')
}}

with source as (
    select * from {{ source('raw', 'bank_reviews_enriched') }}
),

deduplicated as (
    select distinct
        place_id,
        bank_name,
        branch_name,
        region,
        address,
        branch_rating,
        user_rating_count,
        review_text,
        review_rating,
        person_id,
        review_time,
        language,
        sentiment,
        topic
    from source
),

cleaned as (
    select
        place_id as branch_id,
        coalesce(bank_name, 'Unknown Bank') as bank_name,
        coalesce(branch_name, 'Unknown Branch') as branch_name,
        coalesce(region, 'Unknown Region') as region,
        coalesce(address, 'Unknown Address') as address,
        branch_rating,
        coalesce(user_rating_count, 0) as user_rating_count,
        coalesce(review_text, '') as review_text,
        {{ normalize_text('review_text') }},
        coalesce(review_rating, 3) as review_rating,
        coalesce(person_id, 'Unknown Reviewer') as person_id,
        coalesce(review_time, current_timestamp) as review_time,
        coalesce(language, 'unknown') as language,
        coalesce(sentiment, 'neutral') as sentiment,
        coalesce(topic, 'other') as topic
    from deduplicated
)

select * from cleaned
