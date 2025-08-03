-- Tests aliasing and reference rules
-- AL01: aliasing
-- RF01: references
-- RF02: column references
USE DATABASE {{ database_name }};
USE SCHEMA {{ schema_name }};

-- Test table aliasing issues
SELECT 
    customers.customer_id,
    customers.name,
    orders.order_date,
    orders.total_amount
FROM customers
JOIN orders ON customers.customer_id = orders.customer_id
WHERE customers.created_at > '2023-01-01';

-- Better with aliases
SELECT 
    c.customer_id,
    c.name,
    o.order_date,
    o.total_amount
FROM customers AS c
JOIN orders AS o ON c.customer_id = o.customer_id
WHERE c.created_at > '2023-01-01';