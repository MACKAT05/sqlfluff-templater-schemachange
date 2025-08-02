#!/usr/bin/env python3
"""
Extract the exact working pattern from the dataform plugin.
The test showed it DOES work - SQLFluff found it, just missing dataform CLI.
"""

def test_config_loading():
    """Test proper way to load SQLFluff config."""
    print("=== Testing Config Loading ===")
    
    try:
        from sqlfluff.core.config import FluffConfig
        
        # Try different ways to load config
        config = FluffConfig(overrides={'templater': 'dataform-full', 'dialect': 'bigquery'})
        print(f"✅ Direct config creation works")
        print(f"   Templater: {config.get('templater')}")
        print(f"   Dialect: {config.get('dialect')}")
        
        # Test if config can find the templater
        print(f"   Available templaters check...")
        
        # The key question: how does SQLFluff validate available templaters?
        
    except Exception as e:
        print(f"❌ Config creation failed: {e}")

def analyze_why_dataform_works():
    """Analyze what makes dataform plugin work where our schemachange doesn't."""
    print("\n=== Why Dataform Works vs Schemachange ===")
    
    # Test 1: Package registration difference
    try:
        import sqlfluff_templater_dataform_full
        print(f"✅ Dataform package: {sqlfluff_templater_dataform_full.__name__}")
        print(f"   Location: {sqlfluff_templater_dataform_full.__file__}")
        
        # Check what makes it discoverable
        from sqlfluff.core.plugin.host import get_plugin_manager
        pm = get_plugin_manager()
        
        plugins = pm.get_plugins()
        dataform_plugins = [p for p in plugins if 'dataform' in str(p)]
        print(f"   Found in plugin manager: {len(dataform_plugins)} entries")
        for p in dataform_plugins:
            print(f"     - {p}")
            
    except Exception as e:
        print(f"❌ Dataform analysis failed: {e}")
    
    # Test 2: Hook registration difference
    try:
        hook_results = pm.hook.get_templaters()
        print(f"\n✅ Hook system results: {len(hook_results)} groups")
        
        for i, result in enumerate(hook_results):
            if isinstance(result, list):
                names = [t.name for t in result if hasattr(t, 'name')]
                print(f"   Group {i}: {names}")
                if 'dataform-full' in names:
                    print(f"     ⭐ Dataform found in group {i}")
        
    except Exception as e:
        print(f"❌ Hook analysis failed: {e}")

def test_templater_instantiation():
    """Test if we can create templater instances."""
    print("\n=== Testing Templater Instantiation ===")
    
    try:
        from sqlfluff_templater_dataform_full.templater import DataformTemplaterFull
        from sqlfluff.core.config import FluffConfig
        
        config = FluffConfig(overrides={'dialect': 'bigquery'})
        
        # Try to create the templater instance
        templater = DataformTemplaterFull(config=config)
        print(f"✅ Dataform templater created: {templater}")
        print(f"   Name: {templater.name}")
        
    except Exception as e:
        print(f"❌ Templater instantiation failed: {e}")
        import traceback
        traceback.print_exc()

def compare_with_schemachange():
    """Compare the working dataform pattern with our schemachange attempt."""
    print("\n=== Comparing Patterns ===")
    
    # Dataform pattern
    print("DATAFORM (WORKING):")
    print("  ✅ Installed as proper package")
    print("  ✅ Has @hookimpl get_templaters()")
    print("  ✅ Found in plugin manager")
    print("  ✅ Found in hook system")
    print("  ✅ SQLFluff recognizes templater name")
    print("  ❌ Only fails on external dependency (dataform CLI)")
    
    # Our pattern
    print("\nSCHEMACHANGE (NOT WORKING):")
    print("  ❌ Local module, not installed package")  
    print("  ❌ Not found in plugin manager")
    print("  ❌ SQLFluff says 'not available'")
    print("  ✅ Hook pattern looks correct")
    
    print("\n🔍 KEY DIFFERENCE: Package installation and registration!")

def extract_installation_pattern():
    """Extract how dataform plugin gets registered with SQLFluff."""
    print("\n=== Installation Pattern Analysis ===")
    
    try:
        import pkg_resources
        
        # Find the dataform distribution
        for dist in pkg_resources.working_set:
            if 'dataform' in dist.project_name.lower():
                print(f"📦 Package: {dist.project_name} v{dist.version}")
                print(f"   Location: {dist.location}")
                
                # Check entry points
                entry_map = dist.get_entry_map()
                print(f"   Entry point groups: {list(entry_map.keys())}")
                
                if 'sqlfluff' in entry_map:
                    sqlfluff_entries = entry_map['sqlfluff']
                    print(f"   SQLFluff entries: {list(sqlfluff_entries.keys())}")
                    for name, ep in sqlfluff_entries.items():
                        print(f"     {name}: {ep}")
                        
                print("   🎯 THIS IS THE KEY: Entry point registration!")
                break
                
    except Exception as e:
        print(f"❌ Installation analysis failed: {e}")

def main():
    """Extract the complete working pattern."""
    print("Extracting Working Pattern from Dataform Plugin")
    print("=" * 60)
    
    test_config_loading()
    analyze_why_dataform_works()
    test_templater_instantiation()
    compare_with_schemachange()
    extract_installation_pattern()
    
    print("\n" + "=" * 60)
    print("🎯 CONCLUSION:")
    print("The dataform plugin WORKS because it's a properly installed package")
    print("with correct entry point registration. Our schemachange plugin fails")
    print("because it's just a local module without package installation.")

if __name__ == "__main__":
    main()