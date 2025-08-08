USE WAREHOUSE {{ env_var("SNOWFLAKE_WAREHOUSE") }};
USE DATABASE {{ env_var("TEST_DB") }};

CREATE TABLE test_table (
    id INTEGER,
    env_info VARCHAR(100) DEFAULT '{{ env_var("ENVIRONMENT", ) }}'
);
