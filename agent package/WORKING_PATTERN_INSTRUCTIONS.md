# SQLFluff Templater Plugin - Working Pattern Instructions

## Problem Verification: ✅ CONFIRMED

We tested the real dataform plugin and found it **WORKS perfectly**. SQLFluff recognizes it and attempts to use it (failing only due to missing `dataform` CLI). This proves there IS a working pattern.

## Key Test Results

### Dataform Plugin (WORKING) ✅
```
✅ Found in plugin manager: 1 entries  
✅ Hook system results: 2 groups - dataform-full found in group 0
✅ SQLFluff recognizes templater name in config
✅ Lint command attempts to use templater (fails only on CLI dependency)
```

### Our Schemachange Plugin (FAILING) ❌  
```
❌ Not found in plugin manager
❌ SQLFluff says templater 'not available'
❌ Local module, not installed package
```

## The EXACT Working Pattern

Based on analysis of the working dataform plugin:

### 1. Package Installation (CRITICAL)
```
📦 Package: sqlfluff-templater-dataform-full v0.1.3
   Entry point groups: ['sqlfluff']  
   SQLFluff entries: ['sqlfluff_templater_dataform_full']
     sqlfluff_templater_dataform_full: sqlfluff_templater_dataform_full = sqlfluff_templater_dataform_full
```

**KEY INSIGHT**: The plugin MUST be installed as a proper Python package with entry points in the `[sqlfluff]` group.

### 2. Entry Point Configuration
In `pyproject.toml`:
```toml
[project.entry-points.sqlfluff]
your_package_name = "your_package_name"
```

### 3. Hook Registration Code (`__init__.py`)
```python
from sqlfluff.core.plugin import hookimpl
from your_package.templater import YourTemplaterClass

@hookimpl
def get_templaters():
    return [YourTemplaterClass]
```

### 4. Templater Class (`templater.py`)
```python
from sqlfluff.core.templaters.base import RawTemplater, TemplatedFile, RawFileSlice

class YourTemplaterClass(RawTemplater):
    name = "your-templater-name"
    
    def process(self, *, fname, in_str, config=None, formatter=None):
        # Your templating logic
        return TemplatedFile(...)
```

## Why Our Schemachange Failed

❌ **Local module only** - not installed as package  
❌ **No entry point registration** - SQLFluff plugin manager can't find it  
❌ **Hook system works but disconnected** - plugin manager never calls hooks for unregistered packages  

## Solution Steps

### Option 1: Create Proper Package (Recommended)
1. Create proper package structure
2. Add entry point configuration  
3. Install with `pip install -e .`
4. Test with SQLFluff

### Option 2: Continue Monkey Patch (Quick Fix)
The monkey patch is still valid for immediate testing, but proper package installation is the long-term solution.

## Package Structure Template
```
sqlfluff-templater-schemachange/
├── sqlfluff_templater_schemachange/
│   ├── __init__.py          # Hook registration
│   └── templater.py         # Templater implementation
├── pyproject.toml           # Entry point configuration
└── README.md
```

## Entry Point Configuration Template
```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sqlfluff-templater-schemachange"
version = "0.1.0"
dependencies = ["sqlfluff>=3.4.2"]

[project.entry-points.sqlfluff]
sqlfluff_templater_schemachange = "sqlfluff_templater_schemachange"
```

## Usage After Installation
```ini
[sqlfluff]
templater = schemachange
dialect = snowflake

[sqlfluff:templater:schemachange]
# Your templater config
```

## Verification Commands
```bash
# Check if installed and discoverable
python -c "from sqlfluff.core.plugin.host import get_plugin_manager; pm = get_plugin_manager(); print([str(p) for p in pm.get_plugins() if 'schemachange' in str(p)])"

# Test configuration
sqlfluff lint your_file.sql --config .sqlfluff
```

---

**CONCLUSION**: The dataform plugin proves the pattern works. The issue was package installation, not the hook system or SQLFluff architecture. Your templater approach is correct - it just needs proper packaging.