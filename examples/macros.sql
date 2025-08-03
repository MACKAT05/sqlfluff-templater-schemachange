-- Advanced Jinja macros for schemachange templating
-- These macros can be reused across multiple SQL files

-- Macro to generate a CREATE TABLE statement from a table definition
{% macro create_table(table_def, database, schema) %}
CREATE TABLE {{ database }}.{{ schema }}.{{ table_def.name }} (
  {%- for column in table_def.columns %}
    {{ column.name }} {{ column.type }}
    {%- if column.primary_key %} PRIMARY KEY{% endif %}
    {%- if column.not_null %} NOT NULL{% endif %}
    {%- if column.default %} DEFAULT {{ column.default }}{% endif %}
    {%- if not loop.last %},{% endif %}
  {%- endfor %}
);
{% endmacro %}

-- Macro to generate INSERT statements with sample data
{% macro insert_sample_data(table_name, database, schema, row_count=5) %}
{% if table_name == 'customers' %}
INSERT INTO {{ database }}.{{ schema }}.{{ table_name }} (name, email, phone) VALUES
  {%- for i in range(1, row_count + 1) %}
    ('Customer {{ i }}', 'customer{{ i }}@example.com', '555-000{{ i }}')
    {%- if not loop.last %},{% endif %}
  {%- endfor %};
{% elif table_name == 'products' %}
INSERT INTO {{ database }}.{{ schema }}.{{ table_name }} (name, price, category) VALUES
  {%- for i in range(1, row_count + 1) %}
    ('Product {{ i }}', {{ (i * 10) + 99 }}.99, 'Category {{ (i % 3) + 1 }}')
    {%- if not loop.last %},{% endif %}
  {%- endfor %};
{% endif %}
{% endmacro %}

-- Macro to create indexes based on column types
{% macro create_indexes(table_def, database, schema) %}
{%- for column in table_def.columns %}
  {%- if column.type.startswith('VARCHAR') and column.name in ['name', 'email'] %}
CREATE INDEX idx_{{ table_def.name }}_{{ column.name }} 
ON {{ database }}.{{ schema }}.{{ table_def.name }} ({{ column.name }});
  {%- endif %}
{%- endfor %}
{% endmacro %}

-- Macro for environment-specific settings
{% macro apply_environment_config(env, config) %}
-- Environment: {{ env }}
{% if env == 'PROD' %}
-- Production settings
ALTER SESSION SET QUERY_TIMEOUT = {{ config.retention_days * 24 * 60 }};
CREATE OR REPLACE RESOURCE MONITOR production_monitor;
{% elif env == 'DEV' %}
-- Development settings  
ALTER SESSION SET QUERY_TIMEOUT = {{ config.retention_days * 60 }};
{% endif %}
{% endmacro %}

-- Macro to create foreign key relationships
{% macro create_foreign_keys(database, schema) %}
-- Create foreign key relationships between tables
ALTER TABLE {{ database }}.{{ schema }}.orders 
ADD CONSTRAINT fk_orders_customer_id 
FOREIGN KEY (customer_id) REFERENCES {{ database }}.{{ schema }}.customers(id);
{% endmacro %}