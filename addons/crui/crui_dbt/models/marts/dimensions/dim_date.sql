-- dim_date.sql
-- Gold Layer: Calendar dimension table supporting temporal analysis.
-- Covers year range 2020 to 2035.

with date_spine as (
    select
        generate_series(
            '2020-01-01'::date,
            '2035-12-31'::date,
            '1 day'::interval
        )::date as day_date
),

final as (
    select
        to_char(day_date, 'YYYYMMDD')::int       as date_key,
        day_date,
        extract(year from day_date)::int         as year,
        extract(quarter from day_date)::int      as quarter,
        extract(month from day_date)::int        as month,
        to_char(day_date, 'Month')               as month_name,
        extract(week from day_date)::int         as week_of_year,
        extract(day from day_date)::int          as day_of_month,
        extract(dow from day_date)::int          as day_of_week,
        to_char(day_date, 'Day')                 as day_name,

        -- Working day flag (Mon=1, Fri=5; excludes weekends)
        case
            when extract(dow from day_date) in (0, 6) then false
            else true
        end                                      as is_working_day,

        -- Quarter label
        'Q' || extract(quarter from day_date)::text as quarter_label,

        -- Year-Month label for reporting
        to_char(day_date, 'YYYY-MM')             as year_month

    from date_spine
)

select * from final
