#!/usr/bin/env python3
"""Simple test runner for all static tests."""

import subprocess


def run_test(test_name, test_script):
    """Run a single test and return result."""
    print(f"Running {test_name}...")

    try:
        result = subprocess.run(
            ["python", test_script], capture_output=True, text=True, check=True
        )
        print(f"{test_name} passed")
        print(result)
        return True
    except subprocess.CalledProcessError as e:
        print(f"{test_name} failed")
        print(result)
        print(f"Error: {e.stderr}")
        return False


def main():
    """Run all tests."""
    print("Running all static tests...")
    print()

    tests = [
        ("Basic functionality", "test_basic.py"),
        ("Modules support", "test_modules.py"),
        ("Environment variables", "test_env_vars.py"),
        ("Conditional logic", "test_conditional.py"),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_script in tests:
        if run_test(test_name, test_script):
            passed += 1
        print()

    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("All tests passed! Our package is working correctly.")
    else:
        print("Some tests failed. Please check the implementation.")

    return passed == total


if __name__ == "__main__":
    main()
