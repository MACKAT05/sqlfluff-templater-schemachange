CREATE TABLE events (
    id INTEGER,
    {% if environment == 'prod' -%}
    sensitive_data VARCHAR(255),
    {%- endif -%}
    {% if debug_mode %}
    debug_info VARCHAR(1000),
    {%- endif -%}
    created_at TIMESTAMP
);
