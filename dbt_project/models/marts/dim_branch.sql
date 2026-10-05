select distinct
    branch_id,
    branch_name,
    bank_name,
    region,
    address,
    branch_rating,
    user_rating_count
from {{ ref('int_bank_reviews') }}
