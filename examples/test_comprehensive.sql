-- Comprehensive test with multiple template variables and common SQL issues
-- Tests multiple SQLFluff rules with schemachange templating
USE DATABASE {{ database_name }};
USE SCHEMA {{ schema_name }};

-- Create a table with various issues
CREATE TABLE {{ table_name }} (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP
);

-- Insert some test data
INSERT INTO {{ table_name }} (
    name,
    email,
    phone,
    address,
    city,
    state,
    zip_code
) VALUES 
    ('John Doe', 'john@example.com', '555-1234', '123 Main St', 'Anytown', 'CA', '12345'),
    ('Jane Smith', 'jane@example.com', '555-5678', '456 Oak Ave', 'Somewhere', 'NY', '67890');

-- Query with various formatting issues that SQLFluff should catch
SELECT 
    id,name,email,phone 
FROM {{ table_name }} 
WHERE state='{{ state_filter }}' 
AND created_at>='{{ start_date }}'
ORDER BY name,id ;

-- Better formatted version
SELECT 
    id,
    name,
    email,
    phone
FROM {{ table_name }}
WHERE state = '{{ state_filter }}'
    AND created_at >= '{{ start_date }}'
ORDER BY name, id;