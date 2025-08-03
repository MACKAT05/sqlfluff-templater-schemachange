-- Advanced table creation using macros and complex templating
-- This demonstrates macro usage, conditional logic, and advanced Jinja features

{% from "audit_macros.sql" import audit_columns, create_scd_table, environment_setup, log_execution, add_data_tags %}

-- Set up environment
{{ environment_setup() }}

{{ log_execution('V1.0.2_start') }}

-- Create customer SCD table using macro
{{ create_scd_table('dim_customer_scd', 'customer_key', [
    {'name': 'first_name', 'type': 'VARCHAR(100)'},
    {'name': 'last_name', 'type': 'VARCHAR(100)'},
    {'name': 'email', 'type': 'VARCHAR(255)', 'not_null': true},
    {'name': 'phone', 'type': 'VARCHAR(20)'},
    {'name': 'address_line1', 'type': 'VARCHAR(255)'},
    {'name': 'city', 'type': 'VARCHAR(100)'},
    {'name': 'state', 'type': 'VARCHAR(50)'},
    {'name': 'country', 'type': 'VARCHAR(50)'},
    {'name': 'postal_code', 'type': 'VARCHAR(20)'}
]) }}

-- Create events fact table with dynamic partitioning
CREATE TABLE {{ table_prefix }}events (
    event_id INTEGER AUTOINCREMENT PRIMARY KEY,
    customer_id INTEGER,
    event_type VARCHAR(50) NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,

    -- Dynamic columns based on event types
    {% for event_type, fields in {
        'purchase': ['product_id INTEGER', 'amount DECIMAL(10,2)', 'currency VARCHAR(3)'],
        'page_view': ['page_url VARCHAR(500)', 'referrer VARCHAR(500)', 'session_id VARCHAR(255)'],
        'login': ['login_method VARCHAR(50)', 'ip_address VARCHAR(45)', 'user_agent VARCHAR(1000)']
    }.items() %}

    -- {{ event_type | title }} event fields
        {% for field in fields %}
    {{ field }},
        {% endfor %}
    {% endfor %}

    -- Additional metadata
    event_metadata JSON,

    {{ audit_columns() }}

) {% if performance.clustering_keys.events %}
CLUSTER BY ({{ performance.clustering_keys.events | join(', ') }})
{% endif %};

-- Create aggregation tables for different time periods
{% for period, date_func in {
    'daily': 'DATE_TRUNC(day, event_timestamp)',
    'weekly': 'DATE_TRUNC(week, event_timestamp)',
    'monthly': 'DATE_TRUNC(month, event_timestamp)'
}.items() %}

CREATE TABLE {{ table_prefix }}events_{{ period }}_summary (
    summary_id INTEGER AUTOINCREMENT PRIMARY KEY,
    summary_date DATE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_count INTEGER NOT NULL,
    unique_customers INTEGER NOT NULL,

    {% if period == 'daily' %}
    -- Add hourly breakdown for daily summaries
    hour_0 INTEGER DEFAULT 0,
    hour_1 INTEGER DEFAULT 0,
    hour_2 INTEGER DEFAULT 0,
    hour_3 INTEGER DEFAULT 0,
    hour_4 INTEGER DEFAULT 0,
    hour_5 INTEGER DEFAULT 0,
    hour_6 INTEGER DEFAULT 0,
    hour_7 INTEGER DEFAULT 0,
    hour_8 INTEGER DEFAULT 0,
    hour_9 INTEGER DEFAULT 0,
    hour_10 INTEGER DEFAULT 0,
    hour_11 INTEGER DEFAULT 0,
    hour_12 INTEGER DEFAULT 0,
    hour_13 INTEGER DEFAULT 0,
    hour_14 INTEGER DEFAULT 0,
    hour_15 INTEGER DEFAULT 0,
    hour_16 INTEGER DEFAULT 0,
    hour_17 INTEGER DEFAULT 0,
    hour_18 INTEGER DEFAULT 0,
    hour_19 INTEGER DEFAULT 0,
    hour_20 INTEGER DEFAULT 0,
    hour_21 INTEGER DEFAULT 0,
    hour_22 INTEGER DEFAULT 0,
    hour_23 INTEGER DEFAULT 0,
    {% endif %}

    {{ audit_columns() }}
);

-- Create unique constraint for the summary table
ALTER TABLE {{ table_prefix }}events_{{ period }}_summary
ADD CONSTRAINT uk_{{ period }}_summary
UNIQUE (summary_date, event_type);

{% endfor %}

-- Create external integration tables based on configuration
{% if external_systems.salesforce %}
CREATE TABLE {{ staging_prefix }}salesforce_accounts (
    sf_account_id VARCHAR(18) PRIMARY KEY,
    account_name VARCHAR(255),
    account_type VARCHAR(50),
    industry VARCHAR(100),
    annual_revenue DECIMAL(15,2),
    employee_count INTEGER,

    -- Salesforce metadata
    sf_created_date TIMESTAMP,
    sf_last_modified_date TIMESTAMP,

    {{ audit_columns() }}
);

COMMENT ON TABLE {{ staging_prefix }}salesforce_accounts
IS 'Salesforce account data from {{ external_systems.salesforce.instance_url }}';
{% endif %}

{% if external_systems.hubspot %}
CREATE TABLE {{ staging_prefix }}hubspot_contacts (
    hubspot_contact_id INTEGER PRIMARY KEY,
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company VARCHAR(255),
    job_title VARCHAR(200),
    lifecycle_stage VARCHAR(50),

    -- HubSpot specific fields
    hs_created_date TIMESTAMP,
    hs_last_modified_date TIMESTAMP,
    portal_id INTEGER DEFAULT {{ external_systems.hubspot.portal_id }},

    {{ audit_columns() }}
);
{% endif %}

-- Create data quality monitoring table
CREATE TABLE metadata_data_quality_checks (
    check_id INTEGER AUTOINCREMENT PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL,
    check_type VARCHAR(50) NOT NULL, -- 'row_count', 'null_check', 'duplicate_check', etc.
    check_query TEXT NOT NULL,
    expected_result VARCHAR(255),
    actual_result VARCHAR(255),
    status VARCHAR(20) NOT NULL, -- 'PASS', 'FAIL', 'WARNING'
    check_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    {{ audit_columns() }}
);

-- Add data classification tags to sensitive tables
{{ add_data_tags('dim_customer_scd', 'PII') }}
{{ add_data_tags(table_prefix + 'events', 'INTERNAL') }}

{% if external_systems.salesforce %}
{{ add_data_tags(staging_prefix + 'salesforce_accounts', 'CONFIDENTIAL') }}
{% endif %}

-- Create views for analysts with row-level security if enabled
{% if features.enable_row_level_security and environment == 'prod' %}

CREATE OR REPLACE ROW ACCESS POLICY customer_access_policy AS (region VARCHAR(50))
RETURNS BOOLEAN ->
    CASE
        WHEN CURRENT_ROLE() = 'ADMIN' THEN TRUE
        WHEN CURRENT_ROLE() = 'ANALYST_US' AND region = 'us-west-2' THEN TRUE
        WHEN CURRENT_ROLE() = 'ANALYST_EU' AND region = 'eu-west-1' THEN TRUE
        ELSE FALSE
    END;

-- Apply row access policy to events table
ALTER TABLE {{ table_prefix }}events
SET ROW ACCESS POLICY customer_access_policy ON (region);

{% endif %}

-- Create materialized views for common queries (only in non-dev environments)
{% if environment != 'dev' %}

CREATE MATERIALIZED VIEW {{ view_prefix }}customer_event_summary AS
SELECT
    c.customer_id,
    c.customer_key,
    c.first_name,
    c.last_name,
    COUNT(e.event_id) AS total_events,
    COUNT(DISTINCT e.event_type) AS unique_event_types,
    MIN(e.event_timestamp) AS first_event,
    MAX(e.event_timestamp) AS last_event,
    SUM(CASE WHEN e.event_type = 'purchase' THEN 1 ELSE 0 END) AS purchase_events,
    SUM(CASE WHEN e.event_type = 'page_view' THEN 1 ELSE 0 END) AS page_view_events
FROM {{ table_prefix }}customers c
LEFT JOIN {{ table_prefix }}events e ON c.customer_id = e.customer_id
WHERE c.created_at >= DATEADD(day, -{{ business_rules.retention_days }}, CURRENT_DATE)
GROUP BY c.customer_id, c.customer_key, c.first_name, c.last_name;

{% endif %}

-- Grant permissions based on environment and roles
{% set role_permissions = {
    'prod': {
        'ANALYST': ['SELECT'],
        'DATA_ENGINEER': ['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
        'ADMIN': ['ALL']
    },
    'staging': {
        'DEVELOPER': ['SELECT', 'INSERT', 'UPDATE'],
        'DATA_ENGINEER': ['ALL']
    },
    'dev': {
        'DEVELOPER': ['ALL']
    }
} %}

{% for role, permissions in role_permissions.get(environment, {}).items() %}
    {% for permission in permissions %}
        {% if permission == 'ALL' %}
GRANT ALL ON ALL TABLES IN SCHEMA {{ schema_name }} TO ROLE {{ role }};
        {% else %}
GRANT {{ permission }} ON ALL TABLES IN SCHEMA {{ schema_name }} TO ROLE {{ role }};
        {% endif %}
    {% endfor %}
{% endfor %}

{{ log_execution('V1.0.2_complete', 'SUCCESS') }}
