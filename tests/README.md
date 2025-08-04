# Tests Directory

This directory contains test files for the sqlfluff-templater-schemachange project.

## Directory Structure

- `ci/` - CI-specific tests for verifying GitHub Actions workflows
  - `test_ci_fixes.py` - Tests for the three main CI issues that were fixed:
    1. SQLFluff render with directory paths
    2. compare_outputs.py script failures
    3. Windows PowerShell syntax issues

## Running Tests

To run the CI tests:

```bash
python tests/ci/test_ci_fixes.py
```

This will:
1. Generate test files using `test_generator.py`
2. Test basic render functionality
3. Test advanced render functionality with directory structure
4. Test examples render functionality
5. Test that linting failures are handled correctly (expected behavior)

## Test Files

Test files are generated in the `temp/` directory and cleaned up automatically.
The tests verify that the CI fixes work correctly across different scenarios.
