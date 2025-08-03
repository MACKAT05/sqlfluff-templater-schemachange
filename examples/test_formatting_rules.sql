-- Tests various formatting rules
-- LT01: spacing issues
-- LT02: indentation
-- LT05: commas
-- ST06: column order
USE DATABASE {{ database_name }};
USE SCHEMA {{ schema_name }};

CREATE TABLE products(
    id    INTEGER  ,
  name VARCHAR(255),
    description TEXT,
  price DECIMAL(10,2)  ,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)  ;

-- Test bad formatting
SELECT id,name,description 
FROM   products 
WHERE price>100 
AND   name IS NOT NULL;

-- Test better formatting
SELECT 
    id,
    name,
    description,
    price
FROM products
WHERE price > 100
    AND name IS NOT NULL;