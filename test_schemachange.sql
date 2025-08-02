-- Test SQL file with schemachange templating
CREATE TABLE {{ database }}.{{ schema }}.test_table (
    id INTEGER,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Test with environment variable (if available)
-- GRANT SELECT ON {{ database }}.{{ schema }}.test_table TO ROLE {{ env_var('DB_ROLE', 'PUBLIC') }};