-- Repeatable script to create/update analytical views
-- This demonstrates repeatable scripts in schemachange with complex templating

{% from "audit_macros.sql" import environment_setup %}

{{ environment_setup() }}

-- Customer analytics view
CREATE OR REPLACE VIEW {{ view_prefix }}customer_analytics AS
SELECT 
    c.customer_id,
    c.customer_key,
    c.first_name || ' ' || c.last_name AS full_name,
    c.email,
    c.registration_date,
    
    -- Calculate customer lifetime value
    COALESCE(s.total_purchases, 0) AS total_purchases,
    COALESCE(s.total_spent, 0) AS total_spent,
    COALESCE(s.avg_order_value, 0) AS avg_order_value,
    
    -- Customer segmentation
    CASE 
        WHEN s.total_spent >= 1000 THEN 'VIP'
        WHEN s.total_spent >= 500 THEN 'Premium'
        WHEN s.total_spent >= 100 THEN 'Regular'
        ELSE 'New'
    END AS customer_segment,
    
    -- Recency metrics
    s.last_purchase_date,
    DATEDIFF(day, s.last_purchase_date, CURRENT_DATE) AS days_since_last_purchase,
    
    -- Environment-specific fields
    {% if environment == 'dev' %}
    'DEV_CUSTOMER' AS data_source,
    {% else %}
    'PRODUCTION' AS data_source,
    {% endif %}
    
    CURRENT_TIMESTAMP AS view_refreshed_at

FROM {{ table_prefix }}customers c
LEFT JOIN (
    SELECT 
        customer_id,
        COUNT(*) AS total_purchases,
        SUM(total_amount) AS total_spent,
        AVG(total_amount) AS avg_order_value,
        MAX(sale_date) AS last_purchase_date
    FROM {{ table_prefix }}sales
    GROUP BY customer_id
) s ON c.customer_id = s.customer_id;

-- Product performance view
CREATE OR REPLACE VIEW {{ view_prefix }}product_performance AS
SELECT 
    p.product_id,
    p.product_sku,
    p.product_name,
    p.category,
    p.brand,
    p.unit_price,
    
    -- Sales metrics
    COALESCE(ps.units_sold, 0) AS units_sold,
    COALESCE(ps.revenue_generated, 0) AS revenue_generated,
    COALESCE(ps.unique_customers, 0) AS unique_customers,
    
    -- Performance ratios
    CASE 
        WHEN p.unit_cost > 0 THEN 
            ROUND((p.unit_price - p.unit_cost) / p.unit_cost * 100, 2)
        ELSE 0 
    END AS profit_margin_percent,
    
    -- Rankings within category
    RANK() OVER (
        PARTITION BY p.category 
        ORDER BY ps.revenue_generated DESC
    ) AS category_revenue_rank,
    
    ps.last_sale_date,
    
    {% if business_rules.enable_auditing %}
    -- Audit information
    p.created_at AS product_created_at,
    CURRENT_TIMESTAMP AS view_refreshed_at
    {% endif %}

FROM {{ table_prefix }}products p
LEFT JOIN (
    SELECT 
        product_id,
        SUM(quantity) AS units_sold,
        SUM(total_amount) AS revenue_generated,
        COUNT(DISTINCT customer_id) AS unique_customers,
        MAX(sale_date) AS last_sale_date
    FROM {{ table_prefix }}sales
    GROUP BY product_id
) ps ON p.product_id = ps.product_id;

-- Time-based sales analysis view
CREATE OR REPLACE VIEW {{ view_prefix }}sales_trends AS
SELECT 
    DATE_TRUNC('month', sale_date) AS month,
    COUNT(*) AS transaction_count,
    SUM(total_amount) AS monthly_revenue,
    AVG(total_amount) AS avg_transaction_value,
    COUNT(DISTINCT customer_id) AS unique_customers,
    COUNT(DISTINCT product_id) AS unique_products_sold,
    
    -- Year-over-year comparison
    LAG(SUM(total_amount), 12) OVER (ORDER BY DATE_TRUNC('month', sale_date)) AS revenue_same_month_last_year,
    
    -- Calculate growth rate
    CASE 
        WHEN LAG(SUM(total_amount), 12) OVER (ORDER BY DATE_TRUNC('month', sale_date)) > 0 THEN
            ROUND((SUM(total_amount) - LAG(SUM(total_amount), 12) OVER (ORDER BY DATE_TRUNC('month', sale_date))) 
                  / LAG(SUM(total_amount), 12) OVER (ORDER BY DATE_TRUNC('month', sale_date)) * 100, 2)
        ELSE NULL
    END AS yoy_growth_percent,
    
    -- Regional breakdown
    region,
    
    CURRENT_TIMESTAMP AS view_refreshed_at

FROM {{ table_prefix }}sales
WHERE sale_date >= DATEADD(month, -{{ business_rules.retention_days // 30 }}, CURRENT_DATE)
GROUP BY DATE_TRUNC('month', sale_date), region
ORDER BY month DESC, region;

-- Event analytics view (if events table exists)
{% if 'events' in ['events'] %}  {# Simple check - in real usage, you'd query information_schema #}
CREATE OR REPLACE VIEW {{ view_prefix }}event_analytics AS
SELECT 
    event_type,
    DATE_TRUNC('day', event_timestamp) AS event_date,
    COUNT(*) AS event_count,
    COUNT(DISTINCT customer_id) AS unique_users,
    
    -- Hourly distribution
    {% for hour in range(24) %}
    SUM(CASE WHEN EXTRACT(hour FROM event_timestamp) = {{ hour }} THEN 1 ELSE 0 END) AS hour_{{ '%02d'|format(hour) }}_count,
    {% endfor %}
    
    -- Device/platform breakdown (if available in metadata)
    COUNT(CASE WHEN event_metadata:device_type = 'mobile' THEN 1 END) AS mobile_events,
    COUNT(CASE WHEN event_metadata:device_type = 'desktop' THEN 1 END) AS desktop_events,
    COUNT(CASE WHEN event_metadata:device_type = 'tablet' THEN 1 END) AS tablet_events,
    
    CURRENT_TIMESTAMP AS view_refreshed_at

FROM {{ table_prefix }}events
WHERE event_timestamp >= DATEADD(day, -30, CURRENT_DATE)
GROUP BY event_type, DATE_TRUNC('day', event_timestamp)
ORDER BY event_date DESC, event_type;
{% endif %}

-- Create a summary dashboard view
CREATE OR REPLACE VIEW {{ view_prefix }}business_dashboard AS
SELECT 
    'metrics' AS metric_type,
    
    -- Key business metrics
    (SELECT COUNT(*) FROM {{ table_prefix }}customers) AS total_customers,
    (SELECT COUNT(*) FROM {{ table_prefix }}products) AS total_products,
    (SELECT COUNT(*) FROM {{ table_prefix }}sales WHERE sale_date >= CURRENT_DATE - 30) AS sales_last_30_days,
    (SELECT SUM(total_amount) FROM {{ table_prefix }}sales WHERE sale_date >= CURRENT_DATE - 30) AS revenue_last_30_days,
    
    -- Growth metrics
    (SELECT COUNT(*) FROM {{ table_prefix }}customers WHERE created_at >= CURRENT_DATE - 30) AS new_customers_last_30_days,
    
    -- Data quality metrics
    (SELECT COUNT(*) FROM {{ table_prefix }}customers WHERE email IS NULL) AS customers_missing_email,
    (SELECT COUNT(*) FROM {{ table_prefix }}sales WHERE total_amount <= 0) AS invalid_sales_records,
    
    -- Environment info
    '{{ environment }}' AS environment,
    '{{ region }}' AS region,
    CURRENT_TIMESTAMP AS dashboard_refreshed_at;

-- Add comments to views
COMMENT ON VIEW {{ view_prefix }}customer_analytics IS 'Customer analytics with segmentation and lifetime value calculations';
COMMENT ON VIEW {{ view_prefix }}product_performance IS 'Product sales performance with rankings and profitability metrics';
COMMENT ON VIEW {{ view_prefix }}sales_trends IS 'Monthly sales trends with year-over-year growth analysis';
COMMENT ON VIEW {{ view_prefix }}business_dashboard IS 'High-level business metrics dashboard for {{ environment }} environment';

-- Grant appropriate view permissions
{% if environment == 'prod' %}
GRANT SELECT ON {{ view_prefix }}customer_analytics TO ROLE ANALYST;
GRANT SELECT ON {{ view_prefix }}product_performance TO ROLE ANALYST;
GRANT SELECT ON {{ view_prefix }}sales_trends TO ROLE ANALYST;
GRANT SELECT ON {{ view_prefix }}business_dashboard TO ROLE ANALYST;
{% else %}
GRANT ALL ON {{ view_prefix }}customer_analytics TO ROLE DEVELOPER;
GRANT ALL ON {{ view_prefix }}product_performance TO ROLE DEVELOPER;
GRANT ALL ON {{ view_prefix }}sales_trends TO ROLE DEVELOPER;
GRANT ALL ON {{ view_prefix }}business_dashboard TO ROLE DEVELOPER;
{% endif %}