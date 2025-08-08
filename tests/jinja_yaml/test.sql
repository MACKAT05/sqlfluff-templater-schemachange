USE WAREHOUSE {{ warehouse }};
USE DATABASE {{ database_name }};

CREATE TABLE test_table (
    id INTEGER,
    env_info VARCHAR(100) DEFAULT '{{ environment }}'
);
