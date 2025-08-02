#!/usr/bin/env python3
"""Debug script to test schemachange templater."""

from sqlfluff.core.config import FluffConfig
from sqlfluff_templater_schemachange import SchemachangeTemplater

def main():
    print("=== Debugging Schemachange Templater ===")
    
    # Load config
    config = FluffConfig.load_config_file('.sqlfluff')
    print(f"Config loaded:")
    print(f"  Templater: {config.get('templater')}")
    print(f"  Dialect: {config.get('dialect')}")
    
    # Check templater config section
    templater_config = config.get_section(("sqlfluff", "templater", "schemachange"))
    print(f"  Templater config: {templater_config}")
    
    # Create templater instance
    templater = SchemachangeTemplater(config=config)
    print(f"  Templater created: {templater.name}")
    
    # Test templating
    test_sql = "CREATE TABLE {{ database }}.{{ schema }}.test_table (id INTEGER);"
    print(f"\nTest SQL: {test_sql}")
    
    try:
        # Use the template method
        result = templater.template("test.sql", test_sql, config)
        print(f"✅ Template result: {result.templated_str}")
    except Exception as e:
        print(f"❌ Template error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()