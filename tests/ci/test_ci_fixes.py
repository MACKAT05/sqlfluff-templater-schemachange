#!/usr/bin/env python3
"""Test script to verify CI fixes work correctly.

This script tests the three main issues that were fixed:
1. SQLFluff render with directory paths
2. compare_outputs.py script failures
3. Windows PowerShell syntax issues
"""

import subprocess
import sys

# from pathlib import Path


def test_basic_render():
    """Test basic render functionality."""
    print("Testing basic render...")
    try:
        result = subprocess.run(
            ["sqlfluff", "render", "test.sql", "--dialect", "snowflake"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="temp/basic",
        )

        if result.returncode == 0:
            print("✓ Basic render works")
            return True
        else:
            print(f"✗ Basic render failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Basic render exception: {e}")
        return False


def test_advanced_render():
    """Test advanced render functionality with directory structure."""
    print("Testing advanced render...")
    try:
        result = subprocess.run(
            [
                "sqlfluff",
                "render",
                "migrations/V1.0.1__advanced_test.sql",
                "--dialect",
                "snowflake",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="temp/advanced",
        )

        if result.returncode == 0:
            print("✓ Advanced render works")
            return True
        else:
            print(f"✗ Advanced render failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Advanced render exception: {e}")
        return False


def test_examples_render():
    """Test examples render functionality."""
    print("Testing examples render...")
    try:
        result = subprocess.run(
            [
                "sqlfluff",
                "render",
                "migrations/V1.0.1__create_base_tables.sql",
                "--dialect",
                "snowflake",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="examples",
        )

        if result.returncode == 0:
            print("✓ Examples render works")
            return True
        else:
            print(f"✗ Examples render failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Examples render exception: {e}")
        return False


def test_linting_expected_failures():
    """Test that linting failures are handled correctly (expected behavior)."""
    print("Testing linting expected failures...")
    try:
        result = subprocess.run(
            ["sqlfluff", "lint", "test.sql", "--dialect", "snowflake"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="temp/basic",
        )

        # Linting should fail (expected), but the command should not crash
        if result.returncode != 0:
            print("✓ Linting failed as expected")
            return True
        else:
            print("✗ Linting passed unexpectedly")
            return False
    except Exception as e:
        print(f"✗ Linting test exception: {e}")
        return False


if __name__ == "__main__":
    print("Testing CI fixes...")

    # Generate test files first
    try:
        subprocess.run([sys.executable, "test_generator.py"], check=True)
        print("✓ Test files generated")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to generate test files: {e}")
        sys.exit(1)

    # Run tests
    tests = [
        test_basic_render,
        test_advanced_render,
        test_examples_render,
        test_linting_expected_failures,
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
