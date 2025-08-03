-- Advanced Jinja templating test with loops, sets, and macros
-- Tests pure Jinja features without external vars

{% set database_name = 'ANALYTICS_DB' %}
{% set schema_name = 'PUBLIC' %}
{% set environment = 'DEV' %}

-- Define table list with complex structure
{% set table_definitions = [
    {
        'name': 'customers',
        'columns': [
            {'name': 'id', 'type': 'INTEGER', 'primary_key': true},
            {'name': 'name', 'type': 'VARCHAR(255)', 'not_null': true},
            {'name': 'email', 'type': 'VARCHAR(255)'},
            {'name': 'phone', 'type': 'VARCHAR(20)'},
            {'name': 'created_at', 'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP()'}
        ]
    },
    {
        'name': 'orders', 
        'columns': [
            {'name': 'order_id', 'type': 'INTEGER', 'primary_key': true},
            {'name': 'customer_id', 'type': 'INTEGER', 'not_null': true},
            {'name': 'order_date', 'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP()'},
            {'name': 'total_amount', 'type': 'DECIMAL(10,2)'},
            {'name': 'status', 'type': 'VARCHAR(50)', 'default': "'PENDING'"}
        ]
    },
    {
        'name': 'products',
        'columns': [
            {'name': 'product_id', 'type': 'INTEGER', 'primary_key': true},
            {'name': 'name', 'type': 'VARCHAR(255)', 'not_null': true},
            {'name': 'price', 'type': 'DECIMAL(10,2)', 'not_null': true},
            {'name': 'category', 'type': 'VARCHAR(100)'}
        ]
    }
] %}

-- Simple list for testing basic loops
{% set simple_tables = ['users', 'sessions', 'events'] %}

-- Environment-specific configuration
{% set config = {
    'DEV': {'timeout': 300, 'retention_days': 7},
    'PROD': {'timeout': 1800, 'retention_days': 90}
} %}

USE DATABASE {{ database_name }};
USE SCHEMA {{ schema_name }};

-- Environment-specific settings
{% if environment == 'DEV' %}
-- Development configuration
ALTER SESSION SET QUERY_TIMEOUT = {{ config.DEV.timeout }};
ALTER SESSION SET AUTOCOMMIT = TRUE;
{% elif environment == 'PROD' %}
-- Production configuration  
ALTER SESSION SET QUERY_TIMEOUT = {{ config.PROD.timeout }};
ALTER SESSION SET AUTOCOMMIT = FALSE;
{% endif %}

-- Generate CREATE TABLE statements using loops
{% for table_def in table_definitions %}
-- Creating table: {{ table_def.name }}
CREATE TABLE {{ database_name }}.{{ schema_name }}.{{ table_def.name }} (
  {%- for column in table_def.columns %}
    {{ column.name }} {{ column.type }}
    {%- if column.get('primary_key', false) %} PRIMARY KEY{% endif %}
    {%- if column.get('not_null', false) %} NOT NULL{% endif %}
    {%- if column.get('default') %} DEFAULT {{ column.default }}{% endif %}
    {%- if not loop.last %},{% endif %}
  {%- endfor %}
);

{% endfor %}

-- Create simple tables from list
{% for table_name in simple_tables %}
CREATE TABLE {{ database_name }}.{{ schema_name }}.{{ table_name }} (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

{% endfor %}

-- Generate sample INSERT statements with loops
{% for table_def in table_definitions %}
{% if table_def.name == 'customers' %}
-- Sample data for {{ table_def.name }}
INSERT INTO {{ database_name }}.{{ schema_name }}.{{ table_def.name }} (name, email, phone) VALUES
  {%- for i in range(1, 6) %}
    ('Customer {{ i }}', 'customer{{ i }}@example.com', '555-000{{ "%d"|format(i) }}')
    {%- if not loop.last %},{% endif %}
  {%- endfor %};

{% elif table_def.name == 'products' %}
-- Sample data for {{ table_def.name }}
INSERT INTO {{ database_name }}.{{ schema_name }}.{{ table_def.name }} (name, price, category) VALUES
  {%- for i in range(1, 4) %}
    ('Product {{ i }}', {{ (i * 25) + 99 }}.99, 'Category {{ loop.index }}')
    {%- if not loop.last %},{% endif %}
  {%- endfor %};

{% endif %}
{% endfor %}

-- Conditional logic with loops and filters - Snowflake clustering
{% set cluster_columns = ['name', 'email', 'status'] %}
{% for table_def in table_definitions %}
  {%- for column in table_def.columns %}
    {%- if column.name in cluster_columns %}
-- Clustering key for {{ table_def.name }}.{{ column.name }} (Snowflake alternative to indexes)
ALTER TABLE {{ database_name }}.{{ schema_name }}.{{ table_def.name }} 
CLUSTER BY ({{ column.name }});

    {% endif %}
  {%- endfor %}
{% endfor %}

-- Test nested loops and complex logic
{% for table_def in table_definitions %}
  {%- if table_def.name != 'products' %}
    {%- for column in table_def.columns %}
      {%- if column.type.startswith('VARCHAR') %}
-- Column comment for {{ table_def.name }}.{{ column.name }}
COMMENT ON COLUMN {{ database_name }}.{{ schema_name }}.{{ table_def.name }}.{{ column.name }} 
IS 'String column in {{ table_def.name }} table ({{ column.type }})';

      {%- endif %}
    {%- endfor %}
  {%- endif %}
{% endfor %}

-- Test arithmetic and string operations in loops
{% set multipliers = [10, 20, 30] %}
{% for mult in multipliers %}
-- View with multiplier {{ mult }}
CREATE VIEW {{ database_name }}.{{ schema_name }}.revenue_view_{{ mult }} AS
SELECT 
    customer_id,
    SUM(total_amount * {{ mult / 10 }}) AS adjusted_revenue
FROM {{ database_name }}.{{ schema_name }}.orders
GROUP BY customer_id;

{% endfor %}

-- Final cleanup - drop simple tables if in DEV
{% if environment == 'DEV' %}
-- Development cleanup
  {%- for table_name in simple_tables %}
-- DROP TABLE IF EXISTS {{ database_name }}.{{ schema_name }}.{{ table_name }};
  {%- endfor %}
{% endif %}