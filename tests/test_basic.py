#!/usr/bin/env python3
"""Test basic schemachange config reading and variable substitution."""

import os


def test_basic():
    """Test basic functionality with static files."""
    print("Testing basic functionality...")

    # Test rendering
    result = os.system("cd basic && sqlfluff render --config .sqlfluff test.sql")

    if result == 0:
        print("Basic functionality test passed")
        return True
    else:
        print("Basic functionality test failed")
        return False


if __name__ == "__main__":
    test_basic()
