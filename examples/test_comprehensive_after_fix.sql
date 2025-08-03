-- Comprehensive test with multiple template variables and common SQL issues
-- Tests multiple SQLFluff rules with schemachange templating
USE DATABASE {{ database_name }};
USE SCHEMA {{ schema_name }};

-- Create a table with various issues
CREATE TABLE {{ table_name }} (
    ID INTEGER PRIMARY KEY,
    NAME VARCHAR(255) NOT NULL,
    EMAIL VARCHAR(255),
    PHONE VARCHAR(20),
    ADDRESS TEXT,
    CITY VARCHAR(100),
    STATE VARCHAR(2),
    ZIP_CODE VARCHAR(10),
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP
);

-- Insert some test data
INSERT INTO {{ table_name }} (
    NAME,
    EMAIL,
    PHONE,
    ADDRESS,
    CITY,
    STATE,
    ZIP_CODE
) VALUES
(
    'John Doe',
    'john@example.com',
    '555-1234',
    '123 Main St',
    'Anytown',
    'CA',
    '12345'
),
(
    'Jane Smith',
    'jane@example.com',
    '555-5678',
    '456 Oak Ave',
    'Somewhere',
    'NY',
    '67890'
);

-- Query with various formatting issues that SQLFluff should catch
SELECT
    ID,
    NAME,
    EMAIL,
    PHONE
FROM {{ table_name }}
WHERE
    STATE = '{{ state_filter }}'
    AND CREATED_AT >= '{{ start_date }}'
ORDER BY NAME, ID;

-- Better formatted version
SELECT
    ID,
    NAME,
    EMAIL,
    PHONE
FROM {{ table_name }}
WHERE
    STATE = '{{ state_filter }}'
    AND CREATED_AT >= '{{ start_date }}'
ORDER BY NAME, ID;
