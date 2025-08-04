# SQLFluff Templater for Schemachange

A custom SQLFluff templater that provides **schemachange-compatible** Jinja templating features. This templater reads `schemachange-config.yml` files and provides the same templating experience as schemachange without requiring schemachange as a dependency.

> **Note**: This is a **standalone implementation** that replicates schemachange's templating behavior within SQLFluff. It does **not** import or depend on the schemachange package itself.

## Features

- **Schemachange-Compatible Config**: Reads `schemachange-config.yml` files using the same format and structure
- **Jinja2 Templating**: Full SQLFluff JinjaTemplater support with additional schemachange-style functions
- **Variable Management**: Supports complex nested variables exactly like schemachange
- **Environment Variables**: Provides `env_var()` function matching schemachange's implementation
- **Modules Support**: Load templates and macros from folders (schemachange `modules-folder` equivalent)
- **No External Dependencies**: Pure SQLFluff + PyYAML implementation, no schemachange package required

## Why Use This?

This templater is ideal when you want to:
- **Lint schemachange SQL files** with SQLFluff's comprehensive rule set
- **Use existing schemachange configs** without installing the full schemachange toolchain
- **Integrate SQL linting** into CI/CD pipelines that use schemachange for deployments
- **Maintain consistency** between your schemachange templates and SQLFluff linting

The templater replicates schemachange's Jinja environment and config parsing, so your templates work identically in both tools.

## Installation

```bash
pip install sqlfluff-templater-schemachange
```

Or install from source:

```bash
git clone https://github.com/MACKAT05/sqlfluff-templater-schemachange
cd sqlfluff-templater-schemachange
pip install -e .
```

## Configuration

### Basic SQLFluff Configuration

Create a `.sqlfluff` file in your project root:

```ini
[sqlfluff]
templater = schemachange
dialect = snowflake

[sqlfluff:templater:schemachange]
# Path to schemachange config folder (optional, defaults to '.')
config_folder = .

# Schemachange config file name (optional, defaults to 'schemachange-config.yml')
config_file = schemachange-config.yml

# Modules folder for macro loading (optional)
modules_folder = modules

# Additional variables (merged with config file vars)
vars = {"environment": "dev", "schema_suffix": "_DEV"}
```

### Schemachange Configuration

Create a `schemachange-config.yml` file:

```yaml
config-version: 1

# Basic schemachange settings
root-folder: 'scripts'
modules-folder: 'modules'

# Database connection settings
snowflake-account: '{{ env_var("SNOWFLAKE_ACCOUNT") }}'
snowflake-user: '{{ env_var("SNOWFLAKE_USER") }}'
snowflake-role: 'TRANSFORMER'
snowflake-warehouse: 'COMPUTE_WH'
snowflake-database: 'MY_DATABASE'

# Variables for templating
vars:
  database_name: 'MY_DATABASE'
  schema_name: 'ANALYTICS'
  environment: 'production'
  table_prefix: 'fact_'

  # Nested variables
  sources:
    raw_database: 'RAW_DATA'
    staging_database: 'STAGING'

  # Secret variables (automatically filtered from logs)
  secrets:
    api_key: '{{ env_var("API_KEY") }}'
    encryption_key: '{{ env_var("ENCRYPTION_KEY") }}'

# Additional settings
create-change-history-table: false
autocommit: false
verbose: true
```

## Usage Examples

### Basic Variable Templating

**SQL File** (`V1.0.1__create_tables.sql`):
```sql
-- Create tables with dynamic names
CREATE TABLE {{ database_name }}.{{ schema_name }}.{{ table_prefix }}sales (
    id INTEGER,
    customer_id INTEGER,
    amount DECIMAL(10,2),
    created_at TIMESTAMP
);

CREATE TABLE {{ database_name }}.{{ schema_name }}.{{ table_prefix }}customers (
    id INTEGER,
    name VARCHAR(255),
    email VARCHAR(255)
);
```

### Using Nested Variables

```sql
-- Reference nested configuration
CREATE SCHEMA IF NOT EXISTS {{ sources.staging_database }}.INTERMEDIATE;

-- Copy data from raw to staging
CREATE TABLE {{ sources.staging_database }}.INTERMEDIATE.cleaned_data AS
SELECT * FROM {{ sources.raw_database }}.PUBLIC.raw_data
WHERE created_at >= '{{ start_date }}';
```



### Using Jinja Macros

**Macro file** (`modules/common_macros.sql`):
```sql
{% macro create_audit_columns() %}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) DEFAULT CURRENT_USER()
{% endmacro %}

{% macro generate_schema_name(custom_schema_name=none, node=none) %}
    {% if custom_schema_name is none %}
        {{ target.schema }}
    {% else %}
        {{ target.schema }}_{{ custom_schema_name | trim }}
    {% endif %}
{% endmacro %}
```

**SQL file using macros**:
```sql
CREATE TABLE {{ database_name }}.{{ generate_schema_name('analytics') }}.user_events (
    event_id INTEGER,
    user_id INTEGER,
    event_type VARCHAR(50),
    {{ create_audit_columns() }}
);
```

### Environment Variable Integration

Access environment variables using the `env_var()` function:

```sql
-- Use environment variables with defaults
USE WAREHOUSE {{ env_var('SNOWFLAKE_WAREHOUSE', 'DEFAULT_WH') }};
USE DATABASE {{ env_var('DATABASE_NAME', database_name) }};

-- Connect to environment-specific database
USE DATABASE {{ database_name }}_{{ env_var('ENVIRONMENT', 'dev') | upper }};

-- Use secrets from environment
CREATE OR REPLACE EXTERNAL FUNCTION get_data(...)
RETURNS VARIANT
LANGUAGE PYTHON
HANDLER='main'
API_INTEGRATION = {{ env_var('API_INTEGRATION_NAME') }};
```

### Conditional Logic

```sql
CREATE TABLE {{ database_name }}.{{ schema_name }}.events (
    event_id INTEGER,
    user_id INTEGER,
    event_data JSON,

    {% if environment == 'production' %}
    -- Only add PII columns in production
    user_email VARCHAR(255),
    user_phone VARCHAR(20),
    {% endif %}

    created_at TIMESTAMP
);

{% if environment != 'production' %}
-- Add test data in non-production environments
INSERT INTO {{ database_name }}.{{ schema_name }}.events
VALUES (1, 100, '{"test": true}', CURRENT_TIMESTAMP);
{% endif %}
```

### Template Inheritance

**Base template** (`modules/base_table.sql`):
```sql
{% block table_definition %}
CREATE TABLE {{ database_name }}.{{ schema_name }}.{{ table_name }} (
    {% block columns %}{% endblock %}
    {% block audit_columns %}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    {% endblock %}
);
{% endblock %}

{% block post_create %}
-- Default post-creation steps
{% endblock %}
```

**Specific table** (`V1.0.2__create_products.sql`):
```sql
{% extends "base_table.sql" %}
{% set table_name = "products" %}

{% block columns %}
    product_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2),
    category VARCHAR(100),
{% endblock %}

{% block post_create %}
-- Add specific indexes
CREATE INDEX idx_products_category ON {{ database_name }}.{{ schema_name }}.{{ table_name }} (category);
{% endblock %}
```

## Running SQLFluff

Once configured, run SQLFluff as usual:

```bash
# Lint all SQL files
sqlfluff lint

# Lint specific files
sqlfluff lint scripts/versioned/

# Fix auto-fixable issues
sqlfluff fix

# Check specific file with verbose output
sqlfluff lint --verbose V1.0.1__create_tables.sql
```

## Advanced Configuration

### Multiple Environment Support

You can have different configurations for different environments:

**.sqlfluff** (development):
```ini
[sqlfluff:templater:schemachange]
config_folder = configs
config_file = dev-config.yml
vars = {"environment": "dev"}
```

**configs/dev-config.yml**:
```yaml
config-version: 1
vars:
  database_name: 'DEV_DATABASE'
  environment: 'dev'
  debug_mode: true
```

**configs/prod-config.yml**:
```yaml
config-version: 1
vars:
  database_name: 'PROD_DATABASE'
  environment: 'prod'
  debug_mode: false
```

### Macro Loading

Configure macro loading from a modules folder:

```ini
[sqlfluff:templater:schemachange]
modules_folder = templates/macros
```

This allows you to use `{% include %}` and `{% import %}` statements to load macros from the specified folder.

### Integration with CI/CD

**GitHub Actions example**:
```yaml
name: SQL Linting
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install sqlfluff sqlfluff-templater-schemachange

      - name: Lint SQL files
        env:
          SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
          SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
        run: |
          sqlfluff lint scripts/
```

## Secret Handling

The templater automatically identifies and filters secrets from logs based on:

1. Variable names containing "secret" (case-insensitive)
2. Variables nested under a "secrets" key

```yaml
vars:
  api_key_secret: "sensitive_value"  # Filtered
  database_password: "password123"   # Not filtered

  secrets:
    oauth_token: "token123"          # Filtered
    encryption_key: "key456"         # Filtered
```

## Troubleshooting

### Common Issues

1. **Template not found**: Ensure your `modules-folder` is correctly configured
2. **Undefined variable**: Check your `schemachange-config.yml` and CLI `vars`
3. **Permission errors**: Verify file paths and permissions for config and template files

### Debug Mode

Enable verbose logging to see what's happening:

```bash
sqlfluff lint --verbose --debug
```

### Environment Variables

Use environment variables for sensitive configuration:

```bash
export SNOWFLAKE_ACCOUNT="your-account"
export SNOWFLAKE_USER="your-user"
sqlfluff lint
```

## Contributing

### Development Setup

The project uses static tests for easy debugging and CI integration:

```bash
# Clone the repository
git clone https://github.com/MACKAT05/sqlfluff-templater-schemachange
cd sqlfluff-templater-schemachange

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt

# Install pre-commit
pip install pre-commit
pre-commit install
```

The project includes static test files in the `tests/` directory for easy debugging and CI integration.

### Testing

The project includes static test files for easy debugging:

```bash
# Run all tests
python tests/run_tests.py

# Run individual tests
python tests/test_basic.py
python tests/test_modules.py
python tests/test_env_vars.py
python tests/test_conditional.py
```

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes:
   ```bash
   # Run all tests
   python tests/run_tests.py

   # Test SQLFluff integration
   cd tests/basic && sqlfluff render test.sql
   ```
5. Pre-commit hooks will run automatically on `git commit`
6. Submit a pull request

### Note on Pre-commit

The pre-commit configuration uses local SQLFluff hooks that require the development package to be installed first. This avoids the chicken-and-egg problem of trying to install the package from PyPI before it's published.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [SQLFluff](https://github.com/sqlfluff/sqlfluff) - The SQL linter this plugin extends
- [schemachange](https://github.com/Snowflake-Labs/schemachange) - Database change management tool this integrates with
- [Snowflake](https://www.snowflake.com/) - Cloud data platform
