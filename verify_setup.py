#!/usr/bin/env python3
"""Setup Verification Script.

Quick verification that the development environment is working correctly.
"""

import subprocess
import sys
from pathlib import Path


def check_package_installed():
    """Check if the package is installed in development mode."""
    try:
        from sqlfluff_templater_schemachange.templater import SchemachangeTemplater

        print("✅ Package imported successfully")
        print(f"   Templater name: {SchemachangeTemplater.name}")
        return True
    except ImportError as e:
        print(f"❌ Package import failed: {e}")
        return False


def check_sqlfluff_integration():
    """Check SQLFluff integration with the templater."""
    try:
        # SQLFluff needs to run from the examples directory to find the .sqlfluff config
        result = subprocess.run(
            [
                "python",
                "-c",
                (
                    "import os; os.chdir('examples'); "
                    "os.system('sqlfluff render migrations/V1.0.1__create_base_tables.sql --dialect snowflake')"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ SQLFluff integration working")
            print("   Template rendering successful")
            return True
        else:
            print("❌ SQLFluff integration failed")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ SQLFluff integration test failed: {e}")
        return False


def check_test_examples():
    """Check if test examples were generated."""
    temp_dir = Path("temp")
    if temp_dir.exists():
        example_dirs = list(temp_dir.iterdir())
        if len(example_dirs) > 0:
            print(f"✅ Test examples generated ({len(example_dirs)} directories)")
            return True
        else:
            print("❌ No test examples found in temp/")
            return False
    else:
        print("❌ temp/ directory not found")
        return False


def check_pre_commit():
    """Check if pre-commit is installed and configured."""
    try:
        result = subprocess.run(
            ["pre-commit", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("✅ Pre-commit installed")

            # Check if hooks are installed
            git_hooks = Path(".git/hooks/pre-commit")
            if git_hooks.exists():
                print("✅ Pre-commit hooks installed")
                return True
            else:
                print("⚠️  Pre-commit hooks not installed (run: pre-commit install)")
                return False
        else:
            print("❌ Pre-commit not available")
            return False
    except Exception as e:
        print(f"❌ Pre-commit check failed: {e}")
        return False


def main():
    """Run all verification checks."""
    try:
        print("🔍 Verifying development environment setup...")
    except UnicodeEncodeError:
        print("Verifying development environment setup...")
    print()

    checks = [
        ("Package Installation", check_package_installed),
        ("SQLFluff Integration", check_sqlfluff_integration),
        ("Test Examples", check_test_examples),
        ("Pre-commit Setup", check_pre_commit),
    ]

    results = []
    for name, check_func in checks:
        print(f"Checking {name}...")
        result = check_func()
        results.append(result)
        print()

    passed = sum(results)
    total = len(results)

    print("=" * 50)
    try:
        print(f"📊 Verification Results: {passed}/{total} checks passed")
    except UnicodeEncodeError:
        print(f"Verification Results: {passed}/{total} checks passed")

    if passed == total:
        try:
            print("🎉 All checks passed! Development environment is ready.")
        except UnicodeEncodeError:
            print("All checks passed! Development environment is ready.")
    else:
        try:
            print("⚠️  Some checks failed. See output above for details.")
        except UnicodeEncodeError:
            print("Some checks failed. See output above for details.")

        print("\nQuick fixes:")
        if not results[0]:  # Package installation
            print("• Run: pip install -e .")
        if not results[2]:  # Test examples
            print("• Run: python test_generator.py")
            print("• Test scenarios: python test_scenario_runner.py")
        if not results[3]:  # Pre-commit
            print("• Run: pip install pre-commit && pre-commit install")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
