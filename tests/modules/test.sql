{%- from "common.sql" import audit_columns -%}

CREATE TABLE users (
    id INTEGER,
    name VARCHAR(255),
    {{- audit_columns() -}}
);
