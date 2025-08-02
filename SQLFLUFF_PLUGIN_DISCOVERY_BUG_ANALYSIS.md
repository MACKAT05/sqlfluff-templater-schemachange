# SQLFluff Plugin Discovery Bug - Comprehensive Analysis

## Issue Summary

**Bug**: SQLFluff 3.4.2 has a critical integration gap between its plugin system and templater discovery system. Plugin templaters are successfully loaded by the plugin manager but are not made available for use due to a hardcoded templater list.

**Impact**: Custom templater plugins cannot be used, despite being properly registered via Python entry points and successfully loaded by the plugin system.

**Error Message**: 
```
Error loading config: Requested templater 'schemachange' which is not currently available. Try one of raw, jinja, python, placeholder
```

## Root Cause Analysis

### 1. Plugin System Works Correctly ✅
- Entry points are properly registered under the `"sqlfluff"` group
- Plugin manager successfully discovers and loads plugin templaters
- Plugin templater classes are accessible via `get_plugin_manager().get_plugins()`

### 2. Templater Discovery System is Hardcoded ❌
The `core_templaters()` function in `sqlfluff.core.templaters` is hardcoded to only return built-in templaters:

```python
def core_templaters() -> Iterator[type[RawTemplater]]:
    """Returns the templater tuples for the core templaters."""
    yield from [
        RawTemplater,
        JinjaTemplater,
        PythonTemplater,
        PlaceholderTemplater,
    ]
```

### 3. No Integration Between Systems ❌
- The templater selection system calls `core_templaters()` to get available templaters
- `core_templaters()` never checks the plugin system
- Result: Plugin templaters are loaded but not discoverable for configuration

## Evidence

### Plugin System Working
```bash
python -c "from sqlfluff.core.plugin.host import get_plugin_manager; pm = get_plugin_manager(); templaters = [p for p in pm.get_plugins() if hasattr(p, 'name') and hasattr(p, '__bases__')]; print('Plugin templaters:', [(t.__name__, t.name) for t in templaters])"
# Output: Plugin templaters: [('SchemachangeTemplater', 'schemachange')]
```

### Entry Points Registered Correctly
```bash
python -c "import pkg_resources; print([ep.name for ep in pkg_resources.iter_entry_points('sqlfluff')])"
# Output: ['schemachange', 'sqlfluff', 'sqlfluff_rules_aliasing', ...]
```

### Core Templaters Only Shows Built-ins
```bash
python -c "from sqlfluff.core.templaters import core_templaters; print([t.name for t in core_templaters()])"
# Output: ['raw', 'jinja', 'python', 'placeholder']
```

## How SQLFluff Works (Based on Documentation Analysis)

### Configuration Flow
1. **Config Loading**: SQLFluff reads `.sqlfluff` files with hierarchical precedence
2. **Templater Selection**: The `templater = schemachange` config triggers templater lookup
3. **Templater Discovery**: SQLFluff calls `core_templaters()` to get available templaters
4. **Validation**: If requested templater not in `core_templaters()`, error is thrown

### Architecture (From SQLFluff Documentation)
The SQLFluff architecture has 4 main stages:
1. **Stage 1 - Templater**: Converts templated SQL to valid SQL
2. **Stage 2 - Lexer**: Separates SQL into segments
3. **Stage 3 - Parser**: Creates parse tree from segments
4. **Stage 4 - Linter**: Checks parse tree for violations

The bug occurs in **Stage 1** where templater selection happens.

## Current Plugin Ecosystem

Based on my research, I found evidence of other SQLFluff templater plugins:
- `sqlfluff-templater-dbt` (official dbt templater plugin)
- `sqlfluff-templater-dataform-full` (community plugin on PyPI)

This confirms that plugin templaters are an intended feature, but the discovery mechanism is broken.

## Issues Found in GitHub

While I couldn't find direct reports of this specific plugin discovery bug, I found several related issues that confirm the templating system's complexity:

1. **Issue #5371**: Jinja templating layout issues
2. **Issue #5463**: Undefined Jinja variables causing unparsable sections  
3. **Issue #5325**: dbt templater formatting problems
4. **Issue #4449**: dbt compilation errors with ephemeral models

These issues show that templating is a active area of development and bug reports.

## Working Fix (Monkey Patch)

```python
import sqlfluff.core.templaters as templaters_module
from sqlfluff.core.plugin.host import get_plugin_manager
from sqlfluff.core.templaters.base import RawTemplater

# Save original function
_original_core_templaters = templaters_module.core_templaters

def patched_core_templaters():
    """Returns core templaters plus plugin templaters."""
    # Get core templaters
    yield from _original_core_templaters()
    
    # Get plugin templaters
    pm = get_plugin_manager()
    for plugin in pm.get_plugins():
        if hasattr(plugin, 'name') and hasattr(plugin, '__bases__'):
            if issubclass(plugin, RawTemplater):
                yield plugin

# Apply the patch
templaters_module.core_templaters = patched_core_templaters
```

## Proper Fix for SQLFluff

### Location to Modify
File: `src/sqlfluff/core/templaters/__init__.py`

### Proposed Solution
Modify the `core_templaters()` function to include plugin templaters:

```python
def core_templaters() -> Iterator[type[RawTemplater]]:
    """Returns the templater tuples for the core templaters and plugin templaters."""
    # Core templaters
    yield from [
        RawTemplater,
        JinjaTemplater,
        PythonTemplater,
        PlaceholderTemplater,
    ]
    
    # Plugin templaters
    from sqlfluff.core.plugin.host import get_plugin_manager
    pm = get_plugin_manager()
    for plugin in pm.get_plugins():
        if hasattr(plugin, 'name') and hasattr(plugin, '__bases__'):
            # Check if it's a templater (inherits from RawTemplater)
            if issubclass(plugin, RawTemplater):
                yield plugin
```

## Test Environment Details

- **SQLFluff Version**: 3.4.2
- **Python Version**: 3.10
- **OS**: Windows 10
- **Plugin Package**: `sqlfluff-templater-schemachange 0.1.0`
- **Entry Point Group**: `"sqlfluff"`

## Plugin Entry Point Configuration

The plugin was correctly configured in `setup.py`:

```python
entry_points={
    "sqlfluff": [
        "schemachange = sqlfluff_templater_schemachange:SchemachangeTemplater",
    ],
},
```

## Impact Assessment

This bug affects **all custom templater plugins** for SQLFluff 3.4.2, not just our schemachange templater. The plugin system architecture suggests this functionality was intended to work, but the integration was never completed.

## Files to Create/Modify in SQLFluff Fork

### Core Fix
- `src/sqlfluff/core/templaters/__init__.py` - Modify `core_templaters()` function

### Tests
- `test/core/templaters/test_plugin_integration.py` - Add tests for plugin templater discovery
- Add test fixtures with sample plugin templater

### Documentation  
- Update plugin development documentation to clarify templater plugin requirements
- Add examples of custom templater plugins

## Testing Strategy

1. **Unit Tests**: Test that `core_templaters()` includes plugin templaters
2. **Integration Tests**: Test full SQLFluff flow with plugin templater
3. **Regression Tests**: Ensure built-in templaters still work
4. **Edge Cases**: Test plugin loading errors, malformed plugins

## Backwards Compatibility

This fix is **fully backwards compatible**:
- Existing built-in templaters continue to work unchanged
- No breaking changes to existing APIs
- Plugin discovery is purely additive

## Next Steps for Contributing

1. **Fork SQLFluff repository**: https://github.com/sqlfluff/sqlfluff
2. **Create feature branch**: `fix/plugin-templater-discovery`
3. **Implement fix** in `src/sqlfluff/core/templaters/__init__.py`
4. **Add comprehensive tests** to verify plugin integration
5. **Update documentation** about plugin templater development
6. **Submit pull request** with detailed description and test results

## Additional Research Notes

- SQLFluff uses a sophisticated plugin system with entry points
- The `dbt` templater is implemented as a separate plugin package
- Plugin architecture supports rules, templaters, and other extensions
- Configuration system has comprehensive templater-specific sections
- The bug appears to be an oversight rather than intentional design

This represents a significant architectural gap that prevents the intended plugin system from working for templaters, despite working correctly for other plugin types like rules.