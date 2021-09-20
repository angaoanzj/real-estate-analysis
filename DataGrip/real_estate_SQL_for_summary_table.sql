-- get apartment average price change month on month from 09/2020 to 05/2021
-- Same SQL in the section risk management part 2 in the file Analysis_apartment.ipynb
with select_month as (
    -- select properties after 31/08/2020
    select *,
           to_char("sold_Date", 'YYYY-MM') as year_month
    from suburbs_compare_after_092020
    where "sold_Date" > '2020-08-31'
    order by year_month
),
     grouped as (
         --  select apartments and calculate average price grouped by suburbs
         select suburb, year_month, round(avg(price), 2) as avg_price
         from select_month
         where type like 'Apartment%'
         group by 1, 2
         order by 1, 2
     ),
     leftjoin as (
         -- left join grouped tables
         select g1.*,
                g2.year_month                     as latter_year_month,
                g2.avg_price                      as latter_avg_price,
                to_date(g1.year_month, 'YYYY-MM') as former_date,
                to_date(g2.year_month, 'yyyy-mm') as latter_date
         from grouped as g1
                  left join grouped as g2
                            on g1.year_month < g2.year_month and
                               g1.suburb = g2.suburb
         where to_date(g2.year_month, 'YYYY-MM') - to_date(g1.year_month, 'YYYY-MM') = 30
         or to_date(g2.year_month, 'YYYY-MM') - to_date(g1.year_month, 'YYYY-MM') = 31
         or to_date(g2.year_month, 'YYYY-MM') - to_date(g1.year_month, 'YYYY-MM') = 28
         order by g1.suburb, g1.year_month, g2.year_month
     )
select suburb,
       year_month as former_year_month,
       avg_price as former_year_month,
       latter_year_month,
       latter_avg_price,
       concat(year_month, ' with ', latter_year_month)       as month_compared,
       round((latter_avg_price - avg_price) * 100 / avg_price, 2) as change_percentage
from leftjoin;


-- Following SQLs are used to create summary table in the report.
-- min_max_rate select maximum and minimum price change rate month on month from 09/2020 to 05/2020
create table min_max_rate as (
    select suburb,
           max(risk_analysis_after_092020.change_percentage) as max_price_change_rate,
           min(risk_analysis_after_092020.change_percentage) as min_price_change_rate
    from risk_analysis_after_092020
    group by suburb
);
-- calculate average price of apartments in 05/2020
create table avg_price_in_may as (
    select suburb,
           round(avg(price), 2) as avg_price
    from suburbs_affordable
    where year = '2021'
      and month = '5'
      and type like 'Apartment%'
    group by suburb
);
-- select suburbs distance to the city(Melbourne VIC 3000) and affordability percentage in each suburbs
create table distance_percentage as (
    select affordability_suburbs.suburb,
           suburbs_affordable.distance,
           affordability_suburbs.percentage as affordability
    from affordability_suburbs
             inner join suburbs_affordable
                        on affordability_suburbs.suburb = suburbs_affordable.suburb
    group by affordability_suburbs.suburb,
             affordability_suburbs.percentage,
             suburbs_affordable.distance
);
-- select the price change in 05/2021 compare with 09/2020
create table compare_with_may as (
    SELECt suburb,percentage_2021_2020
    from "risk_compare_with_May"
);
-- inner join all the values mentioned above according to the suburbs
with join_all as (
    select distance_percentage.*,
           avg_price_in_may.avg_price            as avg_price,
           compare_with_may.percentage_2021_2020 as price_change_rate_May,
           min_max_rate.max_price_change_rate,
           min_max_rate.min_price_change_rate
    from distance_percentage
             inner join compare_with_may on
        distance_percentage.suburb = compare_with_may.suburb
             inner join avg_price_in_may on
        distance_percentage.suburb = avg_price_in_may.suburb
             inner join min_max_rate on
        distance_percentage.suburb = min_max_rate.suburb
    order by distance
)
select *
from join_all;























