# SQLFluff Schemachange Templater Examples

This directory contains example SQL files that demonstrate the SQLFluff schemachange templater in action, along with various SQLFluff linting rules.

## Files

### SQL Migration Files
- `migrations/V1.0.1__create_base_tables.sql` - Basic table creation with templating
- `migrations/V1.0.2__create_advanced_tables.sql` - Advanced tables with complex Jinja logic
- `migrations/R__create_views.sql` - Repeatable views with templated names

### Template Files
- `templates/audit_macros.sql` - Common audit column macros for reuse

### Configuration Files
- `.sqlfluff` - SQLFluff configuration for these examples
- `schemachange-config.yml` - Schemachange configuration with template variables

## Usage

### Linting Examples
```bash
# Lint a specific migration file
sqlfluff lint migrations/V1.0.1__create_base_tables.sql --config .sqlfluff

# Lint all SQL files in the migrations directory
sqlfluff lint migrations/ --config .sqlfluff

# Get verbose output for complex templating
sqlfluff lint migrations/V1.0.2__create_advanced_tables.sql --config .sqlfluff -v
```

### Fixing Examples
```bash
# Fix formatting issues in a migration
sqlfluff fix migrations/V1.0.1__create_base_tables.sql --config .sqlfluff

# See what would be fixed without applying changes
sqlfluff fix migrations/R__create_views.sql --config .sqlfluff --diff
```

### Testing the Templater
```bash
# Parse and see how templates are processed
sqlfluff parse migrations/V1.0.1__create_base_tables.sql --config .sqlfluff

# Test with different configurations
sqlfluff lint migrations/ --config .sqlfluff
```

## Template Variables

The examples use these template variables (defined in `schemachange-config.yml`):

- `database_name` → `MY_DATABASE`
- `schema_name` → `ANALYTICS`
- `table_name` → `customers`
- `state_filter` → `CA`
- `start_date` → `2023-01-01`
- `environment` → `DEV`

## SQLFluff Rules Demonstrated

### Layout & Formatting (LT rules)
- **LT01**: Spacing around operators and keywords
- **LT02**: Indentation consistency
- **LT05**: Comma placement
- **LT12**: Trailing newline requirements

### Capitalization (CP rules)
- **CP01**: Keyword capitalization
- **CP02**: Identifier capitalization
- **CP03**: Function name capitalization

### References (RF rules)
- **RF01**: Column references
- **RF02**: Table references
- **RF04**: Keywords used as identifiers

### Aliasing (AL rules)
- **AL01**: Table aliasing requirements
- **AL02**: Column aliasing consistency

### Structure (ST rules)
- **ST06**: Column ordering
- **ST07**: Function spacing

## Tips

1. **Start Simple**: Begin with `test_basic_templating.sql` to verify the templater is working
2. **Fix Incrementally**: Use `sqlfluff fix` on one file at a time to understand the changes
3. **Check Diffs**: Use `--diff` flag to preview changes before applying
4. **Customize Rules**: Modify `.sqlfluff` to adjust rule strictness for your needs

## Common Issues

- **Missing Variables**: Ensure all template variables are defined in the schemachange config
- **Path Issues**: Run commands from the examples directory so relative paths work correctly
- **Rule Conflicts**: Some rules may conflict with your coding standards - adjust `.sqlfluff` as needed
