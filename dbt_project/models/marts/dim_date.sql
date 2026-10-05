select distinct
    review_time::date as date_id,
    extract(year from review_time) as year,
    extract(month from review_time) as month,
    extract(dow from review_time) as day_of_week,
    case extract(dow from review_time)
        when 0 then 'Sunday'
        when 1 then 'Monday'
        when 2 then 'Tuesday'
        when 3 then 'Wednesday'
        when 4 then 'Thursday'
        when 5 then 'Friday'
        else 'Saturday'
    end as day_name
from {{ ref('int_bank_reviews') }}
