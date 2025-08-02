-- Create base analytics tables
-- This demonstrates basic variable templating with schemachange

USE DATABASE {{ database_name }};
USE SCHEMA {{ schema_name }};

-- Create customers dimension table
CREATE TABLE {{ table_prefix }}customers (
    customer_id INTEGER PRIMARY KEY,
    customer_key VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    registration_date DATE,
    
    {% if features.enable_data_masking %}
    -- Add masking policy for PII fields when enabled
    CONSTRAINT email_masking MASKING POLICY email_mask,
    CONSTRAINT phone_masking MASKING POLICY phone_mask,
    {% endif %}
    
    -- Audit columns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) DEFAULT CURRENT_USER()
);

-- Create products dimension table  
CREATE TABLE {{ table_prefix }}products (
    product_id INTEGER PRIMARY KEY,
    product_sku VARCHAR(100) UNIQUE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    brand VARCHAR(100),
    unit_cost DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sales fact table with conditional clustering
CREATE TABLE {{ table_prefix }}sales (
    sale_id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES {{ table_prefix }}customers(customer_id),
    product_id INTEGER REFERENCES {{ table_prefix }}products(product_id),
    
    sale_date DATE NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    
    -- Regional information
    region VARCHAR(50) DEFAULT '{{ region }}',
    
    -- Audit trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_system VARCHAR(50) DEFAULT 'SCHEMACHANGE'
    
    {% if performance.clustering_keys.transactions %}
    -- Add clustering for performance
) CLUSTER BY ({{ performance.clustering_keys.transactions | join(', ') }});
    {% else %}
);
    {% endif %}

-- Create indexes for better query performance
{% if environment != 'dev' %}
CREATE INDEX idx_sales_date ON {{ table_prefix }}sales (sale_date);
CREATE INDEX idx_sales_customer ON {{ table_prefix }}sales (customer_id);
{% endif %}

-- Add comments for documentation
COMMENT ON TABLE {{ table_prefix }}customers IS 'Customer dimension table for {{ environment }} environment';
COMMENT ON TABLE {{ table_prefix }}products IS 'Product dimension table with SKU and pricing information';
COMMENT ON TABLE {{ table_prefix }}sales IS 'Sales transaction fact table clustered by {{ performance.clustering_keys.transactions | join(" and ") if performance.clustering_keys.transactions else "sale_date" }}';

-- Grant appropriate permissions based on environment
{% if environment == 'prod' %}
GRANT SELECT ON {{ table_prefix }}customers TO ROLE ANALYST;
GRANT SELECT ON {{ table_prefix }}products TO ROLE ANALYST;
GRANT SELECT ON {{ table_prefix }}sales TO ROLE ANALYST;

GRANT ALL ON {{ table_prefix }}customers TO ROLE DATA_ENGINEER;
GRANT ALL ON {{ table_prefix }}products TO ROLE DATA_ENGINEER;
GRANT ALL ON {{ table_prefix }}sales TO ROLE DATA_ENGINEER;
{% else %}
-- Dev environment - more permissive access
GRANT ALL ON {{ table_prefix }}customers TO ROLE DEVELOPER;
GRANT ALL ON {{ table_prefix }}products TO ROLE DEVELOPER;
GRANT ALL ON {{ table_prefix }}sales TO ROLE DEVELOPER;
{% endif %}