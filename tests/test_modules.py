#!/usr/bin/env python3
"""Test modules/templates folder support."""

import os


def test_modules():
    """Test modules support with static files."""
    print("Testing modules support...")

    # Test rendering
    result = os.system("cd modules && sqlfluff render --config .sqlfluff test.sql")

    if result == 0:
        print("Modules support test passed")
        return True
    else:
        print("Modules support test failed")
        return False


if __name__ == "__main__":
    test_modules()
