# SQLFluff Schemachange Templater Examples

This directory contains example SQL files that demonstrate the SQLFluff schemachange templater in action, along with various SQLFluff linting rules.

## Files

### Test SQL Files
- `test_basic_templating.sql` - Basic template variable substitution
- `test_formatting_rules.sql` - Spacing, indentation, and comma rules
- `test_capitalization.sql` - Keyword and identifier capitalization  
- `test_aliasing_references.sql` - Table aliasing and column reference rules
- `test_comprehensive.sql` - Multiple template variables with various SQL issues

### Configuration Files
- `.sqlfluff` - SQLFluff configuration for these examples
- `schemachange-test-config.yml` - Schemachange configuration with template variables

## Usage

### Linting Examples
```bash
# Lint a specific file
sqlfluff lint test_basic_templating.sql --config .sqlfluff

# Lint all SQL files in the examples directory
sqlfluff lint *.sql --config .sqlfluff

# Get verbose output
sqlfluff lint test_comprehensive.sql --config .sqlfluff -v
```

### Fixing Examples
```bash
# Fix formatting issues
sqlfluff fix test_formatting_rules.sql --config .sqlfluff

# See what would be fixed without applying changes
sqlfluff fix test_capitalization.sql --config .sqlfluff --diff
```

### Testing the Templater
```bash
# See the rendered SQL (what schemachange produces)
schemachange render test_basic_templating.sql --config-folder .

# Compare with SQLFluff's parsing
sqlfluff parse test_basic_templating.sql --config .sqlfluff
```

## Template Variables

The examples use these template variables (defined in `schemachange-test-config.yml`):

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