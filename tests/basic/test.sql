USE DATABASE {{ database_name }};
USE SCHEMA {{ schema_name }};

CREATE TABLE {{ table_name }} (
    id INTEGER,
    name VARCHAR(255)
);
