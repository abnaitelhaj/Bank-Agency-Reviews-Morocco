select
    person_id,
    count(review_id) as total_reviews,
    avg(review_rating) as avg_rating,
    min(review_time) as first_review_date,
    max(review_time) as last_review_date
from {{ ref('int_bank_reviews') }}
group by person_id
