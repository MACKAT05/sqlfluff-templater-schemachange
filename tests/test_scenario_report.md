# Test Scenario Report

Generated: C:\Users\macka\Desktop\sqlfluff-templater-schemachange

## Summary
- Total test scenarios: 12
- Successful: 5
- Failed: 7

## Detailed Results

### advanced ❌ FAIL
- Directory: `temp\advanced`
- Lint tests: 2
- Render tests: 2
- Errors: 4

#### Errors:
- Linting failed for temp\advanced\migrations\V1.0.1__advanced_test.sql
- Linting failed for temp\advanced\templates\common.sql
- Rendering failed for temp\advanced\migrations\V1.0.1__advanced_test.sql
- Rendering failed for temp\advanced\templates\common.sql

### advanced_schemachange ✅ PASS
- Directory: `temp\advanced`
- Lint tests: 0
- Render tests: 2
- Errors: 2

#### Errors:
- Schema failed: temp\advanced\migrations\V1.0.1__advanced_test.sql
- Schema failed: temp\advanced\templates\common.sql

### basic ❌ FAIL
- Directory: `temp\basic`
- Lint tests: 1
- Render tests: 1
- Errors: 2

#### Errors:
- Linting failed for temp\basic\test.sql
- Rendering failed for temp\basic\test.sql

### basic_schemachange ✅ PASS
- Directory: `temp\basic`
- Lint tests: 0
- Render tests: 1
- Errors: 1

#### Errors:
- Schema failed: temp\basic\test.sql

### ci-cd ❌ FAIL
- Directory: `temp\ci-cd`
- Lint tests: 0
- Render tests: 0
- Errors: 1

#### Errors:
- No SQL files found

### ci-cd_schemachange ❌ FAIL
- Directory: `temp\ci-cd`
- Lint tests: 0
- Render tests: 0
- Errors: 1

#### Errors:
- No SQL files found

### complex ❌ FAIL
- Directory: `temp\complex`
- Lint tests: 3
- Render tests: 3
- Errors: 5

#### Errors:
- Linting failed for temp\complex\migrations\V1.0.2__create_products.sql
- Linting failed for temp\complex\templates\base_table.sql
- Linting failed for temp\complex\templates\macros.sql
- Rendering failed for temp\complex\migrations\V1.0.2__create_products.sql
- Rendering failed for temp\complex\templates\base_table.sql

### complex_schemachange ✅ PASS
- Directory: `temp\complex`
- Lint tests: 0
- Render tests: 3
- Errors: 3

#### Errors:
- Schema failed: temp\complex\migrations\V1.0.2__create_products.sql
- Schema failed: temp\complex\templates\base_table.sql
- Schema failed: temp\complex\templates\macros.sql

### environments ❌ FAIL
- Directory: `temp\environments`
- Lint tests: 1
- Render tests: 1
- Errors: 2

#### Errors:
- Linting failed for temp\environments\shared\V1.0.1__env_specific.sql
- Rendering failed for temp\environments\shared\V1.0.1__env_specific.sql

### environments_schemachange ✅ PASS
- Directory: `temp\environments`
- Lint tests: 0
- Render tests: 1
- Errors: 1

#### Errors:
- Schema failed: temp\environments\shared\V1.0.1__env_specific.sql

### test_scenarios ❌ FAIL
- Directory: `temp\test_scenarios`
- Lint tests: 4
- Render tests: 4
- Errors: 6

#### Errors:
- Linting failed for temp\test_scenarios\scenario_01_basic_templating\test.sql
- Linting failed for temp\test_scenarios\scenario_02_env_var_usage\test.sql
- Linting failed for temp\test_scenarios\scenario_04_nested_variables\test.sql
- Rendering failed for temp\test_scenarios\scenario_01_basic_templating\test.sql
- Rendering failed for temp\test_scenarios\scenario_02_env_var_usage\test.sql
- Rendering failed for temp\test_scenarios\scenario_04_nested_variables\test.sql

### test_scenarios_schemachange ✅ PASS
- Directory: `temp\test_scenarios`
- Lint tests: 0
- Render tests: 4
- Errors: 4

#### Errors:
- Schema failed: temp\test_scenarios\scenario_01_basic_templating\test.sql
- Schema failed: temp\test_scenarios\scenario_02_env_var_usage\test.sql
- Schema failed: temp\test_scenarios\scenario_03_conditional_logic\test.sql
- Schema failed: temp\test_scenarios\scenario_04_nested_variables\test.sql
