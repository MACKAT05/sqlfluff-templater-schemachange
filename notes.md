
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

### Entry Points Registered
```bash
python -c "import pkg_resources; print([ep.name for ep in pkg_resources.iter_entry_points('sqlfluff')])"
# Output: ['schemachange', 'sqlfluff', 'sqlfluff_rules_aliasing', ...]
```

### Core Templaters Only Shows Built-ins
```bash
python -c "from sqlfluff.core.templaters import core_templaters; print([t.name for t in core_templaters()])"
# Output: ['raw', 'jinja', 'python', 'placeholder']
```

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
File: `sqlfluff/core/templaters/__init__.py`

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

## Test Environment

- **SQLFluff Version**: 3.4.2
- **Python Version**: 3.10
- **OS**: Windows 10
- **Plugin Package**: `sqlfluff-templater-schemachange 0.1.0`

## Plugin Entry Point Configuration

The plugin was correctly configured in `setup.py`:

```python
entry_points={
    "sqlfluff": [
        "schemachange = sqlfluff_templater_schemachange:SchemachangeTemplater",
    ],
},
```

## Verification Steps

1. **Confirm plugin loading**:
   ```bash
   python -c "from sqlfluff.core.plugin.host import get_plugin_manager; pm = get_plugin_manager(); print([p.__name__ for p in pm.get_plugins() if hasattr(p, 'name')])"
   ```

2. **Test templater discovery before fix**:
   ```bash
   python -c "from sqlfluff.core.templaters import core_templaters; print([t.name for t in core_templaters()])"
   ```

3. **Test templater discovery after fix**:
   ```bash
   # Apply patch, then:
   python -c "from sqlfluff.core.templaters import core_templaters; print([t.name for t in core_templaters()])"
   ```

4. **Test SQLFluff functionality**:
   ```bash
   sqlfluff lint test.sql --templater=schemachange
   ```

## Impact

This bug affects **all custom templater plugins** for SQLFluff 3.4.2, not just our schemachange templater. The plugin system architecture suggests this functionality was intended to work, but the integration was never completed.

## Next Steps

1. Fork SQLFluff repository
2. Create a branch with the fix
3. Add unit tests to verify plugin templater integration
4. Submit pull request to SQLFluff project
5. Test against multiple SQLFluff versions to ensure compatibility

## Files to Create/Modify in SQLFluff Fork

- `sqlfluff/core/templaters/__init__.py` - Modify `core_templaters()` function
- `tests/core/templaters/test_plugin_integration.py` - Add tests for plugin templater discovery
- Update documentation about plugin templater development