# Jinja `extends` Syntax Test

This folder contains test files for Jinja `{% extends %}` and block inheritance syntax in SQL templates.

## Purpose

To check whether SQLFluff and/or schemachange templaters correctly handle Jinja template inheritance (i.e., `{% extends "base.sql" %}` and `{% block ... %}`).

## Known Issues

- As of now, SQLFluff's Jinja templater does **not** reliably support `{% extends %}` syntax for SQL files, even with `templates_dirs` configured. This results in rendering errors or incomplete output.
- The `schemachange` tool does handle this syntax correctly.

## CI Exclusion

This test is **not** included in automated CI check/expect tests due to the above SQLFluff limitation. It is provided for manual or future compatibility testing.

## Files
- `base.sql`: The base template.
- `test.sql`: The child template using `extends`.
- `test.expect`: The expected output if inheritance works.
- `.sqlfluff`: Local config for Jinja templater.

---

If SQLFluff adds support for Jinja inheritance in the future, this test can be re-enabled in CI.
