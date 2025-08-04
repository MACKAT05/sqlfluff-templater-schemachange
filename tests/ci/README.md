# CI Tests

This directory contains tests specifically for verifying GitHub Actions CI/CD workflows.

## test_ci_fixes.py

This test script verifies that the three main CI issues have been fixed:

### Issues Fixed

1. **SQLFluff render with directory paths**
   - **Problem**: CI was calling `sqlfluff render migrations/` but SQLFluff expects file paths
   - **Fix**: Updated CI to iterate through individual files in directories

2. **compare_outputs.py script failures**
   - **Problem**: Script was using absolute paths from wrong directory
   - **Fix**: Updated to use relative paths and run from correct directory

3. **Windows PowerShell syntax**
   - **Problem**: CI used bash syntax (`if command; then`) in PowerShell
   - **Fix**: Restored proper if statement handling for expected lint failures

### Test Coverage

- Basic render functionality
- Advanced render with directory structure
- Examples render functionality
- Linting expected failures (should fail gracefully)

### Usage

```bash
python tests/ci/test_ci_fixes.py
```

The test will generate test files and verify all functionality works correctly.
