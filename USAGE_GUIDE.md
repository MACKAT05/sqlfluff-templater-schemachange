# SQLFluff Schemachange Templater - Complete Usage Guide

This guide provides step-by-step instructions for using the SQLFluff Schemachange Templater to lint SQL files that use schemachange-compatible Jinja templating features.

> **Important**: This templater provides a standalone implementation of schemachange's templating features. It does **not** require or import the schemachange package - it reads `schemachange-config.yml` files directly and replicates the same Jinja environment.

## Quick Start

### 1. Installation

```bash
# Install the templater
pip install sqlfluff-templater-schemachange

# Or install from source
git clone https://github.com/yourusername/sqlfluff-templater-schemachange
cd sqlfluff-templater-schemachange
pip install -e .
```

### 2. Basic Configuration

Create a `.sqlfluff` file in your project root:

```ini
[sqlfluff]
templater = schemachange
dialect = snowflake

[sqlfluff:templater:schemachange]
config_folder = .
modules_folder = .\templates
```

Create a `schemachange-config.yml` file:

```yaml
config-version: 1
vars:
  database_name: 'MY_DATABASE'
  schema_name: 'ANALYTICS'
  environment: 'dev'
```

### 3. Test with a Simple SQL File

Create `test.sql`:

```sql
USE DATABASE {{ database_name }};
USE SCHEMA {{ schema_name }};

CREATE TABLE customers (
    id INTEGER,
    name VARCHAR(255)
);
```

### 4. Run SQLFluff

```bash
sqlfluff lint test.sql
```

## Architecture Overview

The schemachange templater integrates with SQLFluff's templating system by:

1. **Configuration Loading**: Reads `schemachange-config.yml` with environment variable substitution
2. **Variable Extraction**: Merges variables from config file and CLI arguments
3. **Jinja Environment Setup**: Creates a Jinja environment with proper search paths and functions
4. **Template Rendering**: Processes SQL files using Jinja2 templating
5. **Secret Filtering**: Automatically filters sensitive variables from logs

## Configuration Deep Dive

### SQLFluff Configuration Options

```ini
[sqlfluff:templater:schemachange]
# Path to schemachange config (auto-discovered if not specified)
config_file = schemachange-config.yml

# Additional variables (merged with config file vars)
vars = {"debug_mode": true, "linting": true}


# Additional template search paths
modules_folder = templates

```

### Schemachange Config Features

The templater supports all schemachange configuration features:

#### Environment Variables
```yaml
snowflake-account: '{{ env_var("SNOWFLAKE_ACCOUNT") }}'
database_name: '{{ env_var("DATABASE", "DEFAULT_DB") }}'
```

#### Complex Variables
```yaml
vars:
  sources:
    raw: 'RAW_DATABASE'
    staging: 'STAGING_DATABASE'

  features:
    enable_masking: '{{ env_var("ENABLE_MASKING", "false") | bool }}'

  secrets:
    api_key: '{{ env_var("API_KEY") }}'  # Automatically filtered from logs
```

#### Modules Support
```yaml
modules-folder: 'templates'
```

## Advanced Features

### 1. Secret Filtering

Variables are automatically treated as secrets if:
- Name contains "secret" (case-insensitive)
- Nested under a "secrets" key

```yaml
vars:
  api_key_secret: "sensitive"     # Filtered
  password: "123"                 # Not filtered
  secrets:
    token: "abc123"              # Filtered
```

### 2. Macro Templates

Create reusable macros in your modules folder:

**templates/common.sql**:
```sql
{% macro audit_columns() %}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
{% endmacro %}
```

**Usage in SQL files**:
```sql
{% from "common.sql" import audit_columns %}

CREATE TABLE users (
    id INTEGER,
    name VARCHAR(255),
    {{ audit_columns() }}
);
```

### 4. Conditional Logic

```sql
CREATE TABLE events (
    id INTEGER,
    {% if environment == 'prod' %}
    sensitive_data VARCHAR(255),
    {% endif %}
    created_at TIMESTAMP
);
```

### 5. Template Inheritance

**Base template** (`templates/base_table.sql`):
```sql
{% block table_definition %}
CREATE TABLE {{ table_name }} (
    {% block columns %}{% endblock %}
    {% block audit_columns %}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    {% endblock %}
);
{% endblock %}
```

**Child template**:
```sql
{% extends "base_table.sql" %}
{% set table_name = "products" %}

{% block columns %}
    id INTEGER PRIMARY KEY,
    name VARCHAR(255)
{% endblock %}
```

## Real-World Examples

### Environment-Specific Configuration

**Development** (`.sqlfluff`):
```ini
[sqlfluff:templater:schemachange]
config_folder = configs
config_file = dev.yml
vars = {"environment": "dev", "debug": true}
```

**Production** (CI/CD):
```ini
[sqlfluff:templater:schemachange]
config_folder = configs
config_file = prod.yml
vars = {"environment": "prod", "debug": false}
```

### Complex Migration Script

```sql
{% from "macros.sql" import create_scd_table, environment_setup %}

{{ environment_setup() }}

-- Create customer dimension with SCD Type 2
{{ create_scd_table('dim_customer', 'customer_key', [
    {'name': 'first_name', 'type': 'VARCHAR(100)'},
    {'name': 'last_name', 'type': 'VARCHAR(100)'},
    {'name': 'email', 'type': 'VARCHAR(255)', 'not_null': true}
]) }}

-- Environment-specific grants
{% if environment == 'prod' %}
GRANT SELECT ON dim_customer TO ROLE ANALYST_PROD;
{% else %}
GRANT ALL ON dim_customer TO ROLE DEVELOPER;
{% endif %}
```

### CI/CD Integration

**GitHub Actions**:
```yaml
name: SQL Linting
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install sqlfluff sqlfluff-templater-schemachange

      - name: Lint SQL files
        env:
          SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
          DATABASE_NAME: ${{ secrets.DATABASE_NAME }}
        run: sqlfluff lint --dialect snowflake migrations/
```

## Troubleshooting

### Common Issues

#### 1. Template Not Found
```
Error: TemplateNotFound: common.sql
```

**Solution**: Check your `modules-folder` configuration and file paths.

#### 2. Undefined Variable
```
Error: Undefined variable 'database_name'
```

**Solution**: Add the variable to your `schemachange-config.yml` or CLI `vars`.

#### 3. Permission Errors
```
Error: FileNotFoundError: schemachange-config.yml
```

**Solution**: Ensure the config file path is correct and accessible.

### Debug Mode

Enable verbose logging:

```bash
sqlfluff lint --verbose --debug migrations/
```

Check what variables are being loaded:

```python
# Add to your config for debugging
vars:
  debug_variables: true
```

### Validation

Test your templates without running schemachange:

```bash
# Use the render command (if available)
sqlfluff render V1.0.1__test.sql

# Or create a simple test script
python -c "
from jinja2 import Template
import yaml

with open('schemachange-config.yml') as f:
    config = yaml.safe_load(f)

with open('V1.0.1__test.sql') as f:
    template = Template(f.read())

print(template.render(**config['vars']))
"
```

## Performance Optimization

### 1. Template Caching

The templater caches Jinja environments and templates. For large projects:

```ini
[sqlfluff:templater:schemachange]
# Limit template search paths to improve performance
modules_folder = templates
```

### 2. Selective Linting

For large projects, use selective linting:

```bash
# Lint only changed files
sqlfluff lint $(git diff --name-only --diff-filter=AM | grep '\.sql$')

# Lint specific directories
sqlfluff lint migrations/versioned/
```

### 3. Parallel Processing

Use SQLFluff's parallel processing:

```bash
sqlfluff lint --processes 4 migrations/
```

## Integration with Development Workflow

### 1. Pre-commit Hooks

**.pre-commit-config.yaml**:
```yaml
repos:
  - repo: https://github.com/sqlfluff/sqlfluff
    rev: 2.0.0
    hooks:
      - id: sqlfluff-lint
        additional_dependencies: ['sqlfluff-templater-schemachange']
      - id: sqlfluff-fix
        additional_dependencies: ['sqlfluff-templater-schemachange']
```

### 2. VS Code Integration

**.vscode/settings.json**:
```json
{
    "sqlfluff.executablePath": "sqlfluff",
    "sqlfluff.config": ".sqlfluff",
    "sqlfluff.linter.run": "onSave"
}
```

### 3. Make/Task Integration

**Makefile**:
```makefile
lint-sql:
	sqlfluff lint --dialect snowflake migrations/

fix-sql:
	sqlfluff fix --dialect snowflake migrations/

check-sql: lint-sql
	@echo "SQL linting complete"
```

## Best Practices

### 1. Configuration Management

- Keep environment-specific configs separate
- Use environment variables for sensitive data
- Version control your `.sqlfluff` and config files

### 2. Template Organization

- Use consistent macro naming conventions
- Group related macros in single files
- Document complex template logic

### 3. Testing

- Test templates with different variable combinations
- Use linting in CI/CD pipelines
- Validate generated SQL in staging environments

### 4. Security

- Never commit secrets to version control
- Use the secret filtering features
- Audit template access in production environments

## Migration from Other Systems

### From Plain SQLFluff + Jinja

1. Move Jinja variables to `schemachange-config.yml`
2. Update `.sqlfluff` to use `schemachange` templater
3. Test with existing SQL files

### From Manual Schema Management

1. Create initial `schemachange-config.yml` with current settings
2. Add versioning to existing SQL files
3. Gradually adopt templating features

## Support and Community

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive guides and API reference
- **Examples**: Real-world usage examples and templates

This completes the comprehensive setup for integrating schemachange's Jinja templating system with SQLFluff's linting capabilities.
