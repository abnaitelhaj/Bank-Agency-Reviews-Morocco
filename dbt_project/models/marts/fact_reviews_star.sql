select
    review_id,
    branch_id,
    person_id,
    review_time::date as date_id,
    review_text,
    cleaned_text,
    review_rating,
    language,
    topic,
    sentiment,
    satisfaction_level,
    review_sequence_per_user
from {{ ref('int_bank_reviews') }}
