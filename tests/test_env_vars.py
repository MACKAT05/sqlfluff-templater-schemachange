#!/usr/bin/env python3
"""Test environment variable functions."""

import os


def test_env_vars():
    """Test environment variables with static files."""
    print("Testing environment variables...")

    # Test rendering
    result = os.system("cd env_vars && sqlfluff render --config .sqlfluff test.sql")

    if result == 0:
        print("Environment variables test passed")
        return True
    else:
        print("Environment variables test failed")
        return False


if __name__ == "__main__":
    test_env_vars()
