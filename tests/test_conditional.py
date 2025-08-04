#!/usr/bin/env python3
"""Test conditional logic with environment variables."""

import os


def test_conditional():
    """Test conditional logic with static files."""
    print("Testing conditional logic...")

    # Test rendering
    result = os.system("cd conditional && sqlfluff render --config .sqlfluff test.sql")

    if result == 0:
        print("Conditional logic test passed")
        return True
    else:
        print("Conditional logic test failed")
        return False


if __name__ == "__main__":
    test_conditional()
