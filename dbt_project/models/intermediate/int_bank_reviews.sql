{{
    config(materialized='view')
}}

select
    {{ dbt_utils.generate_surrogate_key(['branch_id', 'person_id', 'review_time']) }} as review_id,
    branch_id,
    bank_name,
    branch_name,
    region,
    address,
    branch_rating,
    user_rating_count,
    review_text,
    cleaned_text,
    trimmed_text,
    review_rating,
    person_id,
    review_time,
    language,
    sentiment,
    topic,
    extract(year from review_time) as review_year,
    extract(month from review_time) as review_month,
    extract(dow from review_time) as review_day_of_week,
    case
        when review_rating >= 4 then 'High'
        when review_rating = 3 then 'Medium'
        else 'Low'
    end as satisfaction_level,
    row_number() over (partition by person_id order by review_time) as review_sequence_per_user
from {{ ref('stg_bank_reviews') }}
where person_id is not null
