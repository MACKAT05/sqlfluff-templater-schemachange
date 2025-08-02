#!/usr/bin/env python3
"""
Test the REAL dataform plugin exactly as documented in the README.
This will verify if the plugin actually works as advertised.
"""

import subprocess
import os

def test_dataform_plugin_config():
    """Test if SQLFluff recognizes the dataform-full templater per README."""
    print("=== Testing Real Dataform Plugin (Per README) ===")
    
    # Test 1: Can SQLFluff recognize the templater in config?
    try:
        result = subprocess.run([
            'python', '-c', 
            '''
from sqlfluff.core.config import FluffConfig
config = FluffConfig.load_config_file(".sqlfluff-dataform-test")
print(f"Templater setting: {config.get('templater')}")
print("✅ Config loaded successfully")
            '''
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        print("Config test result:")
        print(f"  Exit code: {result.returncode}")
        print(f"  Output: {result.stdout}")
        if result.stderr:
            print(f"  Error: {result.stderr}")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_dataform_plugin_lint():
    """Test if SQLFluff can actually use the dataform templater to lint files."""
    print("\n=== Testing Dataform Plugin Linting ===")
    
    try:
        # Run SQLFluff lint with dataform templater
        result = subprocess.run([
            'sqlfluff', 'lint', 'test_dataform.sqlx', 
            '--config', '.sqlfluff-dataform-test',
            '--verbose'
        ], capture_output=True, text=True, timeout=30)
        
        print("Lint test result:")
        print(f"  Exit code: {result.returncode}")
        print(f"  Output: {result.stdout}")
        if result.stderr:
            print(f"  Error: {result.stderr}")
        
        # Success is either clean lint (0) or lint errors found (1)
        # Failure would be templater not found (2) or crash
        success = result.returncode in [0, 1]
        if success:
            if "dataform-full" in result.stdout or result.returncode == 0:
                print("✅ Dataform templater appears to be working")
            else:
                print("⚠️  Lint ran but unclear if templater was used")
        else:
            print("❌ Dataform templater failed to run")
            
        return success
        
    except subprocess.TimeoutExpired:
        print("❌ Lint command timed out (may need dataform CLI)")
        return False
    except Exception as e:
        print(f"❌ Lint test failed: {e}")
        return False

def test_templater_discovery():
    """Test how SQLFluff discovers the dataform templater."""
    print("\n=== Testing Templater Discovery Mechanism ===")
    
    try:
        result = subprocess.run([
            'python', '-c',
            '''
import sqlfluff.core.templaters as templaters_module

# Test core templater discovery
core_temps = list(templaters_module.core_templaters())
print(f"Core templaters: {[t.name for t in core_temps]}")

# Check if dataform-full is in core
dataform_in_core = any(t.name == "dataform-full" for t in core_temps)
print(f"dataform-full in core: {dataform_in_core}")

# Test hook system
from sqlfluff.core.plugin.host import get_plugin_manager
pm = get_plugin_manager()
hook_results = pm.hook.get_templaters()

all_from_hooks = []
for result in hook_results:
    if isinstance(result, list):
        all_from_hooks.extend(result)
    else:
        all_from_hooks.append(result)

hook_names = [t.name for t in all_from_hooks if hasattr(t, "name")]
print(f"Hook templaters: {hook_names}")

dataform_in_hooks = "dataform-full" in hook_names
print(f"dataform-full in hooks: {dataform_in_hooks}")

print(f"\\nCONCLUSION:")
if dataform_in_core:
    print("✅ dataform-full found in core templaters")
elif dataform_in_hooks:
    print("⚠️  dataform-full found in hooks but NOT in core")
else:
    print("❌ dataform-full not found anywhere")
            '''
        ], capture_output=True, text=True)
        
        print("Discovery test result:")
        print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
            
        return "dataform-full" in result.stdout
        
    except Exception as e:
        print(f"❌ Discovery test failed: {e}")
        return False

def analyze_working_pattern():
    """If dataform works, analyze what makes it work."""
    print("\n=== Analyzing Working Pattern ===")
    
    try:
        result = subprocess.run([
            'python', '-c',
            '''
import sqlfluff_templater_dataform_full
import inspect
import os

print("=== Dataform Plugin Analysis ===")
print(f"Package location: {sqlfluff_templater_dataform_full.__file__}")
print(f"Package name: {sqlfluff_templater_dataform_full.__name__}")

# Check hook registration
if hasattr(sqlfluff_templater_dataform_full, "get_templaters"):
    templaters = sqlfluff_templater_dataform_full.get_templaters()
    print(f"Hook function returns: {templaters}")
    for t in templaters:
        print(f"  - Templater: {t.name} ({t})")

# Check if it\s registered as a plugin
from sqlfluff.core.plugin.host import get_plugin_manager
pm = get_plugin_manager()
plugins = pm.get_plugins()

dataform_plugin = None
for plugin in plugins:
    if "dataform" in str(plugin).lower():
        dataform_plugin = plugin
        break

if dataform_plugin:
    print(f"Found as plugin: {dataform_plugin}")
    print(f"Plugin type: {type(dataform_plugin)}")
else:
    print("Not found as plugin")

# Check entry points
try:
    import pkg_resources
    for ep in pkg_resources.iter_entry_points("sqlfluff"):
        if "dataform" in ep.name:
            print(f"Entry point: {ep.name} -> {ep.module_name}")
except:
    pass
            '''
        ], capture_output=True, text=True)
        
        print("Pattern analysis:")
        print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Pattern analysis failed: {e}")

def main():
    """Run comprehensive test of the real dataform plugin."""
    print("Testing Real Dataform Plugin (Per README Documentation)")
    print("=" * 60)
    
    results = {
        'config': test_dataform_plugin_config(),
        'lint': test_dataform_plugin_lint(), 
        'discovery': test_templater_discovery()
    }
    
    analyze_working_pattern()
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test}: {status}")
    
    print("\n" + "=" * 60)
    if all(results.values()):
        print("✅ CONCLUSION: Dataform plugin works as documented!")
        print("   This means the issue is specific to our schemachange implementation")
    elif results['discovery'] and not results['config']:
        print("⚠️  CONCLUSION: Plugin discovered but config fails")  
        print("   This suggests SQLFluff core/config integration issue")
    else:
        print("❌ CONCLUSION: Dataform plugin has same issues as our schemachange")
        print("   This confirms a broader SQLFluff plugin system problem")

if __name__ == "__main__":
    main()