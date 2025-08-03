-- Common audit and utility macros for schemachange
-- These macros can be reused across multiple migration scripts

{# Macro to generate standard audit columns #}
{% macro audit_columns() %}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) DEFAULT CURRENT_USER(),
    updated_by VARCHAR(255) DEFAULT CURRENT_USER()
{% endmacro %}

{# Macro to generate data classification tags #}
{% macro add_data_tags(table_name, classification_level='INTERNAL') %}
    {% if features.enable_data_masking %}
    ALTER TABLE {{ table_name }} SET TAG data_classification = '{{ classification_level }}';

        {% if classification_level in data_classification.sensitive_data_tags %}
    ALTER TABLE {{ table_name }} SET TAG sensitive_data = 'true';
    ALTER TABLE {{ table_name }} SET TAG retention_days = '{{ data_classification.pii_retention_days }}';
        {% endif %}
    {% endif %}
{% endmacro %}

{# Macro to create standard indexes #}
{% macro create_standard_indexes(table_name, date_column='created_at', key_columns=[]) %}
    -- Standard date-based index for time-series queries
    CREATE INDEX IF NOT EXISTS idx_{{ table_name }}_{{ date_column }}
    ON {{ table_name }} ({{ date_column }});

    {% for column in key_columns %}
    -- Index for {{ column }}
    CREATE INDEX IF NOT EXISTS idx_{{ table_name }}_{{ column }}
    ON {{ table_name }} ({{ column }});
    {% endfor %}
{% endmacro %}

{# Macro to generate a staging table from source #}
{% macro create_staging_table(source_table, staging_table, transformations={}) %}
    CREATE OR REPLACE TABLE {{ staging_table }} AS
    SELECT
        {% for column, transformation in transformations.items() %}
        {{ transformation }} AS {{ column }},
        {% else %}
        *,
        {% endfor %}
        {{ audit_columns() | replace('DEFAULT CURRENT_TIMESTAMP', 'CURRENT_TIMESTAMP') }}
    FROM {{ source_table }}
    WHERE 1=1
        {% if business_rules.retention_days %}
        AND created_at >= DATEADD(day, -{{ business_rules.retention_days }}, CURRENT_DATE)
        {% endif %}
    ;
{% endmacro %}

{# Macro to generate warehouse usage statement #}
{% macro use_warehouse(operation_type='etl') %}
    {% set warehouse_size = performance.warehouse_sizes.get(operation_type, 'MEDIUM') %}
    USE WAREHOUSE {{ warehouse_size }}_WH;
{% endmacro %}

{# Macro for conditional environment setup #}
{% macro environment_setup() %}
    {% if environment == 'prod' %}
    -- Production environment setup
    SET QUERY_TAG = 'PRODUCTION_DEPLOYMENT';
    USE WAREHOUSE {{ performance.warehouse_sizes.etl }}_WH;

    {% elif environment == 'staging' %}
    -- Staging environment setup
    SET QUERY_TAG = 'STAGING_DEPLOYMENT';
    USE WAREHOUSE {{ performance.warehouse_sizes.analytics }}_WH;

    {% else %}
    -- Development environment setup
    SET QUERY_TAG = 'DEV_DEPLOYMENT';
    USE WAREHOUSE {{ performance.warehouse_sizes.reporting }}_WH;
    {% endif %}

    USE DATABASE {{ database_name }};
    USE SCHEMA {{ schema_name }};
{% endmacro %}

{# Macro to create a slowly changing dimension table #}
{% macro create_scd_table(table_name, business_key, columns=[]) %}
    CREATE TABLE {{ table_name }} (
        {{ table_name }}_id INTEGER AUTOINCREMENT PRIMARY KEY,
        {{ business_key }} VARCHAR(255) NOT NULL,

        {% for column in columns %}
        {{ column.name }} {{ column.type }}{% if column.get('not_null') %} NOT NULL{% endif %},
        {% endfor %}

        -- SCD Type 2 columns
        valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        valid_to TIMESTAMP DEFAULT '2999-12-31 23:59:59',
        is_current BOOLEAN DEFAULT TRUE,
        version_number INTEGER DEFAULT 1,

        {{ audit_columns() }}
    );

    -- Create unique index for current records
    CREATE UNIQUE INDEX idx_{{ table_name }}_current
    ON {{ table_name }} ({{ business_key }})
    WHERE is_current = TRUE;
{% endmacro %}

{# Macro for error handling and logging #}
{% macro log_execution(step_name, status='START') %}
    {% if business_rules.enable_auditing %}
    INSERT INTO {{ database_name }}.METADATA.execution_log (
        step_name,
        status,
        execution_time,
        environment,
        executed_by
    ) VALUES (
        '{{ step_name }}',
        '{{ status }}',
        CURRENT_TIMESTAMP,
        '{{ environment }}',
        CURRENT_USER()
    );
    {% endif %}
{% endmacro %}
