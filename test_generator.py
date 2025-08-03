#!/usr/bin/env python3
"""Test Generator for SQLFluff Schemachange Templater.

This script reads the USAGE_GUIDE.md and generates all the example files
mentioned in the guide into a temp/ folder for testing and verification.
"""

import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


class TestFileGenerator:
    """Generate test files from usage guide examples."""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = Path(temp_dir)
        self.usage_guide_path = Path("USAGE_GUIDE.md")

    def clean_temp_dir(self):
        """Clean the temp directory."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Cleaned and created {self.temp_dir}")

    def extract_code_blocks(self, content: str) -> List[Tuple[str, str, str]]:
        """Extract code blocks from markdown content."""
        # Pattern to match code blocks with optional file names
        pattern = r"```(\w+)?\s*(?:\(([\w\-\.\_\/]+)\))?\s*\n(.*?)\n```"
        matches = re.findall(pattern, content, re.DOTALL)

        code_blocks = []
        for match in matches:
            language = match[0] if match[0] else "text"
            filename = match[1] if match[1] else None
            code = match[2]
            code_blocks.append((language, filename, code))

        return code_blocks

    def extract_named_files(self, content: str) -> Dict[str, str]:
        """Extract files with explicit names from usage guide."""
        files = {}

        # Look for patterns like **filename.ext**:
        pattern = (
            r"\*\*([^\*]+\.(sql|yml|yaml|ini|json|py|md|makefile))"
            r"\*\*:\s*\n```[\w]*\n(.*?)\n```"
        )
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            filename = match[0]
            code = match[2]
            files[filename] = code

        # Also look for Create `filename.ext`: patterns
        pattern2 = (
            r"Create `([^`]+\.(sql|yml|yaml|ini|json|py|md))`:"
            r"\s*\n\n```[\w]*\n(.*?)\n```"
        )
        matches2 = re.findall(pattern2, content, re.DOTALL | re.IGNORECASE)

        for match in matches2:
            filename = match[0]
            code = match[2]
            files[filename] = code

        return files

    def generate_basic_examples(self):
        """Generate basic configuration examples."""

        # Basic .sqlfluff configuration
        basic_sqlfluff = """[sqlfluff]
templater = schemachange
dialect = snowflake

[sqlfluff:templater:schemachange]
config_folder = .
modules_folder = modules
"""

        # Basic schemachange config
        basic_schemachange = """config-version: 1
vars:
  database_name: 'MY_DATABASE'
  schema_name: 'ANALYTICS'
  environment: 'dev'
"""

        # Basic test SQL
        basic_sql = """USE DATABASE {{ database_name }};
USE SCHEMA {{ schema_name }};

CREATE TABLE customers (
    id INTEGER,
    name VARCHAR(255)
);
"""

        self._write_file("basic/.sqlfluff", basic_sqlfluff)
        self._write_file("basic/schemachange-config.yml", basic_schemachange)
        self._write_file("basic/test.sql", basic_sql)
        print("✓ Generated basic examples")

    def generate_advanced_examples(self):
        """Generate advanced configuration examples."""

        # Advanced .sqlfluff config
        advanced_sqlfluff = """[sqlfluff]
templater = schemachange
dialect = snowflake

[sqlfluff:templater:schemachange]
config_file = schemachange-config.yml
vars = {"debug_mode": true, "linting": true}
modules_folder = templates
"""

        # Advanced schemachange config
        advanced_schemachange = """config-version: 1
snowflake-account: '{{ env_var("SNOWFLAKE_ACCOUNT") }}'
database_name: '{{ env_var("DATABASE", "DEFAULT_DB") }}'

vars:
  sources:
    raw: 'RAW_DATABASE'
    staging: 'STAGING_DATABASE'

  features:
    enable_masking: '{{ env_var("ENABLE_MASKING", "false") | bool }}'

  secrets:
    api_key: '{{ env_var("API_KEY") }}'

modules-folder: 'templates'
"""

        # Advanced SQL with macros
        advanced_sql = """{% from "common.sql" import audit_columns %}

CREATE TABLE users (
    id INTEGER,
    name VARCHAR(255),
    {{ audit_columns() }}
);

{% if environment == 'prod' %}
CREATE TABLE events (
    id INTEGER,
    sensitive_data VARCHAR(255),
    created_at TIMESTAMP
);
{% else %}
CREATE TABLE events (
    id INTEGER,
    created_at TIMESTAMP
);
{% endif %}
"""

        # Common macros
        common_macros = """{% macro audit_columns() %}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
{% endmacro %}

{% macro environment_setup() %}
USE WAREHOUSE {{ env_var('SNOWFLAKE_WAREHOUSE', 'DEFAULT_WH') }};
USE DATABASE {{ database_name }};
{% endmacro %}
"""

        self._write_file("advanced/.sqlfluff", advanced_sqlfluff)
        self._write_file("advanced/schemachange-config.yml", advanced_schemachange)
        self._write_file("advanced/migrations/V1.0.1__advanced_test.sql", advanced_sql)
        self._write_file("advanced/templates/common.sql", common_macros)
        print("✓ Generated advanced examples")

    def generate_environment_examples(self):
        """Generate environment-specific examples."""

        # Development config
        dev_sqlfluff = """[sqlfluff:templater:schemachange]
config_folder = configs
config_file = dev.yml
vars = {"environment": "dev", "debug": true}
"""

        dev_config = """config-version: 1
vars:
  database_name: 'DEV_DATABASE'
  environment: 'dev'
  debug_mode: true
"""

        # Production config
        prod_sqlfluff = """[sqlfluff:templater:schemachange]
config_folder = configs
config_file = prod.yml
vars = {"environment": "prod", "debug": false}
"""

        prod_config = """config-version: 1
vars:
  database_name: 'PROD_DATABASE'
  environment: 'prod'
  debug_mode: false
"""

        # Environment-specific SQL
        env_sql = """{{ environment_setup() }}

-- Create customer dimension with SCD Type 2
CREATE TABLE dim_customer (
    customer_key INTEGER,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) NOT NULL
);

-- Environment-specific grants
{% if environment == 'prod' %}
GRANT SELECT ON dim_customer TO ROLE ANALYST_PROD;
{% else %}
GRANT ALL ON dim_customer TO ROLE DEVELOPER;
{% endif %}
"""

        self._write_file("environments/dev/.sqlfluff", dev_sqlfluff)
        self._write_file("environments/dev/configs/dev.yml", dev_config)
        self._write_file("environments/prod/.sqlfluff", prod_sqlfluff)
        self._write_file("environments/prod/configs/prod.yml", prod_config)
        self._write_file("environments/shared/V1.0.1__env_specific.sql", env_sql)
        print("✓ Generated environment examples")

    def generate_complex_examples(self):
        """Generate complex templating examples."""

        # Base template
        base_template = """{% block table_definition %}
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
"""

        # Child template
        child_template = """{% extends "base_table.sql" %}
{% set table_name = "products" %}

{% block columns %}
    product_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2),
    category VARCHAR(100),
{% endblock %}

{% block post_create %}
-- Add specific indexes
CREATE INDEX idx_products_category
ON {{ database_name }}.{{ schema_name }}.{{ table_name }} (category);
{% endblock %}
"""

        # Complex macro file
        complex_macros = """{% macro create_scd_table(table_name, key_column, columns) %}
CREATE TABLE {{ table_name }} (
    {{ key_column }} INTEGER PRIMARY KEY,
    {% for col in columns %}
    {{ col.name }} {{ col.type }}{% if col.get('not_null') %} NOT NULL{% endif %},
    {% endfor %}
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP DEFAULT '9999-12-31 23:59:59',
    is_current BOOLEAN DEFAULT TRUE
);
{% endmacro %}

{% macro environment_setup() %}
USE WAREHOUSE {{ env_var('SNOWFLAKE_WAREHOUSE', 'DEFAULT_WH') }};
USE DATABASE {{ database_name }};
USE SCHEMA {{ schema_name }};
{% endmacro %}
"""

        # Complex configuration
        complex_config = """config-version: 1
vars:
  database_name: 'ANALYTICS_{{ environment | upper }}'
  schema_name: 'CORE'
  environment: '{{ env_var("ENVIRONMENT", "dev") }}'

  sources:
    raw_database: 'RAW_DATA'
    staging_database: 'STAGING_{{ environment | upper }}'

  features:
    enable_masking: '{{ env_var("ENABLE_MASKING", "false") | bool }}'
    enable_row_security: '{{ environment == "prod" }}'

  secrets:
    api_key: '{{ env_var("API_KEY") }}'

modules-folder: 'templates'
"""

        self._write_file("complex/templates/base_table.sql", base_template)
        self._write_file("complex/templates/macros.sql", complex_macros)
        self._write_file("complex/schemachange-config.yml", complex_config)
        self._write_file(
            "complex/migrations/V1.0.2__create_products.sql", child_template
        )
        print("✓ Generated complex examples")

    def generate_ci_cd_examples(self):
        """Generate CI/CD configuration examples."""

        # GitHub Actions workflow
        github_workflow = """name: SQL Linting
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
"""

        # Pre-commit config
        precommit_config = """repos:
  - repo: https://github.com/sqlfluff/sqlfluff
    rev: 2.0.0
    hooks:
      - id: sqlfluff-lint
        additional_dependencies: ['sqlfluff-templater-schemachange']
      - id: sqlfluff-fix
        additional_dependencies: ['sqlfluff-templater-schemachange']
"""

        # VS Code settings
        vscode_settings = """{
    "sqlfluff.executablePath": "sqlfluff",
    "sqlfluff.config": ".sqlfluff",
    "sqlfluff.linter.run": "onSave"
}
"""

        # Makefile
        makefile = """lint-sql:
\tsqlfluff lint --dialect snowflake migrations/

fix-sql:
\tsqlfluff fix --dialect snowflake migrations/

check-sql: lint-sql
\t@echo "SQL linting complete"
"""

        self._write_file("ci-cd/.github/workflows/sql-lint.yml", github_workflow)
        self._write_file("ci-cd/.pre-commit-config.yaml", precommit_config)
        self._write_file("ci-cd/.vscode/settings.json", vscode_settings)
        self._write_file("ci-cd/Makefile", makefile)
        print("✓ Generated CI/CD examples")

    def generate_test_scenarios(self):
        """Generate comprehensive test scenarios for validation."""

        test_scenarios = [
            {
                "name": "basic_templating",
                "description": "Test basic variable substitution",
                "config": {
                    "vars": {
                        "database_name": "TEST_DB",
                        "schema_name": "PUBLIC",
                        "table_name": "test_table",
                    }
                },
                "sql": (
                    "CREATE TABLE {{ database_name }}.{{ schema_name }}."
                    "{{ table_name }} (id INTEGER);"
                ),
            },
            {
                "name": "env_var_usage",
                "description": "Test environment variable functions",
                "config": {
                    "vars": {"database_name": "{{ env_var('TEST_DB', 'DEFAULT_DB') }}"}
                },
                "sql": "USE DATABASE {{ database_name }};\nCREATE TABLE test (id INTEGER);",
            },
            {
                "name": "conditional_logic",
                "description": "Test if/else conditional logic",
                "config": {"vars": {"environment": "dev", "enable_logging": True}},
                "sql": """CREATE TABLE events (
    id INTEGER,
    {% if environment == 'dev' %}
    debug_info VARCHAR(1000),
    {% endif %}
    created_at TIMESTAMP
);""",
            },
            {
                "name": "nested_variables",
                "description": "Test nested variable access",
                "config": {
                    "vars": {"sources": {"raw": "RAW_DB", "staging": "STAGING_DB"}}
                },
                "sql": (
                    "CREATE TABLE {{ sources.staging }}.cleaned_data "
                    "AS SELECT * FROM {{ sources.raw }}.raw_data;"
                ),
            },
        ]

        for i, scenario in enumerate(test_scenarios, 1):
            scenario_dir = f"test_scenarios/scenario_{i:02d}_{scenario['name']}"

            # Create config file
            config_content = f"""config-version: 1
# {scenario['description']}
vars:
{self._format_yaml_vars(scenario['config']['vars'], indent=2)}
"""

            # Create SQL file
            sql_content = f"""-- {scenario['description']}
{scenario['sql']}
"""

            self._write_file(f"{scenario_dir}/schemachange-config.yml", config_content)
            self._write_file(f"{scenario_dir}/test.sql", sql_content)

        print("✓ Generated test scenarios")

    def _format_yaml_vars(self, vars_dict: dict, indent: int = 0) -> str:
        """Format variables as YAML with proper indentation."""
        lines = []
        prefix = " " * indent

        for key, value in vars_dict.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str):
                        lines.append(f"{prefix}  {sub_key}: '{sub_value}'")
                    else:
                        lines.append(f"{prefix}  {sub_key}: {sub_value}")
            elif isinstance(value, str):
                lines.append(f"{prefix}{key}: '{value}'")
            else:
                lines.append(f"{prefix}{key}: {value}")

        return "\n".join(lines)

    def _write_file(self, relative_path: str, content: str):
        """Write content to a file in the temp directory."""
        file_path = self.temp_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def generate_all(self):
        """Generate all test files and examples."""
        try:
            print("🚀 Generating test files from usage guide...")
        except UnicodeEncodeError:
            print("Generating test files from usage guide...")

        self.clean_temp_dir()
        self.generate_basic_examples()
        self.generate_advanced_examples()
        self.generate_environment_examples()
        self.generate_complex_examples()
        self.generate_ci_cd_examples()
        self.generate_test_scenarios()

        # Copy existing examples for comparison
        if Path("examples").exists():
            shutil.copytree("examples", self.temp_dir / "existing_examples")
            print("✓ Copied existing examples for comparison")

        try:
            print(f"\n🎉 Generated comprehensive test suite in {self.temp_dir}/")
            print("📁 Directory structure:")
        except UnicodeEncodeError:
            print(f"\nGenerated comprehensive test suite in {self.temp_dir}/")
            print("Directory structure:")
        self._print_directory_tree(self.temp_dir)

    def _print_directory_tree(
        self, path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0
    ):
        """Print a directory tree structure."""
        if current_depth >= max_depth:
            return

        items = sorted(path.iterdir())
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item.name}")

            if item.is_dir() and current_depth < max_depth - 1:
                extension = "    " if is_last else "│   "
                self._print_directory_tree(
                    item, prefix + extension, max_depth, current_depth + 1
                )


def main():
    """Main entry point."""
    generator = TestFileGenerator()
    generator.generate_all()


if __name__ == "__main__":
    main()
