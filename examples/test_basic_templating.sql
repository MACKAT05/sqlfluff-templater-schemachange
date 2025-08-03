-- Basic templating test
-- Tests: LT12 (trailing newline), RF04 (keywords as identifiers), LT01 (spacing)
USE DATABASE {{ database_name }};
USE SCHEMA {{ schema_name }};

CREATE TABLE customers (
    id INTEGER,
    name VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);