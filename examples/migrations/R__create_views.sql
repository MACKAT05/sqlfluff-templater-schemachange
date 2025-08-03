-- Repeatable script to create/update analytical views
-- This demonstrates repeatable scripts in schemachange with complex templating

{% from "audit_macros.sql" import environment_setup %}

{{ environment_setup() }}

-- Customer analytics view
create or replace view {{ view_prefix }}customer_analytics as
select
    c.customer_id,
    c.customer_key,
    c.first_name || ' ' || c.last_name as full_name,
    c.email,
    c.registration_date,

    -- Calculate customer lifetime value
    coalesce(s.total_purchases, 0) as total_purchases,
    coalesce(s.total_spent, 0) as total_spent,
    coalesce(s.avg_order_value, 0) as avg_order_value,

    -- Customer segmentation
    case
        when s.total_spent >= 1000 then 'VIP'
        when s.total_spent >= 500 then 'Premium'
        when s.total_spent >= 100 then 'Regular'
        else 'New'
    end as customer_segment,

    -- Recency metrics
    s.last_purchase_date,
    datediff(day, s.last_purchase_date, current_date) as days_since_last_purchase,

    -- Environment-specific fields
    {% if environment == 'dev' %}
    'DEV_CUSTOMER' AS data_source,
    {% else %}
    'PRODUCTION' as data_source,
    {% endif %}

    current_timestamp as view_refreshed_at

from {{ table_prefix }}customers as c
    left join (
        select
            customer_id,
            count(*) as total_purchases,
            sum(total_amount) as total_spent,
            avg(total_amount) as avg_order_value,
            max(sale_date) as last_purchase_date
        from {{ table_prefix }}sales
        group by customer_id
    ) as s on c.customer_id = s.customer_id;

-- Product performance view
create or replace view {{ view_prefix }}product_performance as
select
    p.product_id,
    p.product_sku,
    p.product_name,
    p.category,
    p.brand,
    p.unit_price,

    -- Sales metrics
    coalesce(ps.units_sold, 0) as units_sold,
    coalesce(ps.revenue_generated, 0) as revenue_generated,
    coalesce(ps.unique_customers, 0) as unique_customers,

    -- Performance ratios
    case
        when p.unit_cost > 0
            then
                round((p.unit_price - p.unit_cost) / p.unit_cost * 100, 2)
        else 0
    end as profit_margin_percent,

    -- Rankings within category
    rank() over (
        partition by p.category
        order by ps.revenue_generated desc
    ) as category_revenue_rank,

    ps.last_sale_date,

{% if business_rules.enable_auditing %}
-- Audit information
p.created_at as product_created_at,
current_timestamp as view_refreshed_at
{% endif %}

from {{ table_prefix }}products as p
    left join (
        select
            product_id,
            sum(quantity) as units_sold,
            sum(total_amount) as revenue_generated,
            count(distinct customer_id) as unique_customers,
            max(sale_date) as last_sale_date
        from {{ table_prefix }}sales
        group by product_id
    ) as ps on p.product_id = ps.product_id;

-- Time-based sales analysis view
create or replace view {{ view_prefix }}sales_trends as
select
    date_trunc('month', sale_date) as month,
    count(*) as transaction_count,
    sum(total_amount) as monthly_revenue,
    avg(total_amount) as avg_transaction_value,
    count(distinct customer_id) as unique_customers,
    count(distinct product_id) as unique_products_sold,

    -- Year-over-year comparison
    lag(sum(total_amount), 12) over (order by date_trunc('month', sale_date)) as revenue_same_month_last_year,

    -- Calculate growth rate
    case
        when lag(sum(total_amount), 12) over (order by date_trunc('month', sale_date)) > 0
            then
                round(
                    (sum(total_amount) - lag(sum(total_amount), 12) over (order by date_trunc('month', sale_date)))
                    / lag(sum(total_amount), 12) over (order by date_trunc('month', sale_date)) * 100, 2
                )
    end as yoy_growth_percent,

    -- Regional breakdown
    region,

    current_timestamp as view_refreshed_at

from {{ table_prefix }}sales
where sale_date >= dateadd(month, -{{ business_rules.retention_days // 30 }}, current_date)
group by date_trunc('month', sale_date), region
order by month desc, region asc;

-- Event analytics view (if events table exists)
{% if 'events' in ['events'] %}  {# Simple check - in real usage, you'd query information_schema #}
create or replace view {{ view_prefix }}event_analytics as
select
    event_type,
    date_trunc('day', event_timestamp) as event_date,
    count(*) as event_count,
    count(distinct customer_id) as unique_users,

    -- Hourly distribution
    {% for hour in range(24) %}
    sum(case when extract(hour from event_timestamp) = {{ hour }} then 1 else 0 end)
        as hour_{{ '%02d'|format(hour) }}_count,
    {% endfor %}

    -- Device/platform breakdown (if available in metadata)
    count(case when event_metadata:device_type = 'mobile' then 1 end) as mobile_events,
    count(case when event_metadata:device_type = 'desktop' then 1 end) as desktop_events,
    count(case when event_metadata:device_type = 'tablet' then 1 end) as tablet_events,

    current_timestamp as view_refreshed_at

from {{ table_prefix }}events
where event_timestamp >= dateadd(day, -30, current_date)
group by event_type, date_trunc('day', event_timestamp)
order by event_date desc, event_type asc;
{% endif %}

-- Create a summary dashboard view
create or replace view {{ view_prefix }}business_dashboard as
select
    'metrics' as metric_type,

    -- Key business metrics
    (select count(*) from {{ table_prefix }}customers) as total_customers,
    (select count(*) from {{ table_prefix }}products) as total_products,
    (
        select count(*) from {{ table_prefix }}sales
        where sale_date >= current_date - 30
    ) as sales_last_30_days,
    (
        select sum(total_amount) from {{ table_prefix }}sales
        where sale_date >= current_date - 30)
        as revenue_last_30_days,

    -- Growth metrics
    (
        select count(*) from {{ table_prefix }}customers
        where created_at >= current_date - 30)
        as new_customers_last_30_days,

    -- Data quality metrics
    (
        select count(*) from {{ table_prefix }}customers
        where email is NULL
    ) as customers_missing_email,
    (
        select count(*) from {{ table_prefix }}sales
        where total_amount <= 0
    ) as invalid_sales_records,

    -- Environment info
    '{{ environment }}' as environment,
    '{{ region }}' as region,
    current_timestamp as dashboard_refreshed_at;

-- Add comments to views
comment on view {{ view_prefix }}customer_analytics is 'Customer analytics with segmentation and lifetime value calculations';
comment on view {{ view_prefix }}product_performance is 'Product sales performance with rankings and profitability metrics';
comment on view {{ view_prefix }}sales_trends is 'Monthly sales trends with year-over-year growth analysis';
comment on view {{ view_prefix }}business_dashboard is 'High-level business metrics dashboard for {{ environment }} environment';

-- Grant appropriate view permissions
{% if environment == 'prod' %}
GRANT SELECT ON {{ view_prefix }}customer_analytics TO ROLE ANALYST;
GRANT SELECT ON {{ view_prefix }}product_performance TO ROLE ANALYST;
GRANT SELECT ON {{ view_prefix }}sales_trends TO ROLE ANALYST;
GRANT SELECT ON {{ view_prefix }}business_dashboard TO ROLE ANALYST;
{% else %}
grant all on {{ view_prefix }}customer_analytics to role developer;
grant all on {{ view_prefix }}product_performance to role developer;
grant all on {{ view_prefix }}sales_trends to role developer;
grant all on {{ view_prefix }}business_dashboard to role developer;
{% endif %}
