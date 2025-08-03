#!/usr/bin/env python3
"""Development Environment Setup Script.

This script sets up the development environment for the SQLFluff Schemachange Templater.
It handles the installation order to avoid the chicken-and-egg problem with pre-commit.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description, check=True):
    """Run a command and handle output."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, capture_output=True, text=True
        )
        if result.stdout.strip():
            print(f"   {result.stdout.strip()}")
        if result.returncode == 0:
            print(f"✅ {description} completed")
        else:
            print(f"⚠️  {description} completed with warnings")
            if result.stderr.strip():
                print(f"   {result.stderr.strip()}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"   {e.stderr.strip()}")
        return False


def main():
    """Set up the development environment."""
    try:
        print("🚀 Setting up SQLFluff Schemachange Templater development environment")
    except UnicodeEncodeError:
        print("Setting up SQLFluff Schemachange Templater development environment")
    print()

    # Check if we're in the right directory
    if not Path("setup.py").exists():
        try:
            print(
                "❌ Error: setup.py not found. "
                "Please run this script from the project root."
            )
        except UnicodeEncodeError:
            print(
                "Error: setup.py not found. "
                "Please run this script from the project root."
            )
        sys.exit(1)

    try:
        print("📋 Development setup checklist:")
    except UnicodeEncodeError:
        print("Development setup checklist:")
    print("   1. Upgrade pip")
    print("   2. Install package in development mode")
    print("   3. Install development dependencies")
    print("   4. Install pre-commit hooks")
    print("   5. Generate test examples")
    print("   6. Run initial tests")
    print()

    success = True

    # Step 1: Upgrade pip
    success &= run_command(
        f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"
    )

    # Step 2: Install package in development mode (critical for pre-commit)
    success &= run_command(
        f"{sys.executable} -m pip install -e .",
        "Installing package in development mode",
    )

    # Step 3: Install development dependencies
    success &= run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing development dependencies",
    )

    # Step 4: Install pre-commit
    success &= run_command(
        f"{sys.executable} -m pip install pre-commit", "Installing pre-commit"
    )

    # Step 5: Install pre-commit hooks
    success &= run_command("pre-commit install", "Installing pre-commit hooks")

    # Step 6: Generate test examples
    success &= run_command(
        f"{sys.executable} test_generator.py", "Generating test examples"
    )

    # Step 7: Run comprehensive verification
    print("🧪 Running comprehensive verification...")
    test_success = run_command(
        f"{sys.executable} verify_setup.py", "Running verification script", check=False
    )

    print()
    print("=" * 60)
    if success and test_success:
        try:
            print("🎉 Development environment setup completed successfully!")
            print()
            print("📝 You're now ready to develop! Next steps:")
        except UnicodeEncodeError:
            print("Development environment setup completed successfully!")
            print()
            print("You're now ready to develop! Next steps:")
        print("   • Make your changes to the code")
        print("   • Add tests in temp/ directory with: python test_generator.py")
        print("   • Run tests with: python setup_test_environments.py")
        print("   • Pre-commit hooks will run automatically on git commit")
        print()
        try:
            print("🔧 Useful commands:")
        except UnicodeEncodeError:
            print("Useful commands:")
        print("   • sqlfluff lint examples/migrations/ --dialect snowflake")
        print("   • sqlfluff render temp/basic/test.sql")
        print("   • pre-commit run --all-files")
        print("   • pytest (when you add tests)")
    else:
        try:
            print(
                "⚠️  Setup completed with some issues. "
                "Please check the output above."
            )
        except UnicodeEncodeError:
            print("Setup completed with some issues. Please check the output above.")
        print("   The development environment should still be functional.")

    print()
    try:
        print("📚 For more information, see:")
    except UnicodeEncodeError:
        print("For more information, see:")
    print("   • README.md - Project overview and usage")
    print("   • USAGE_GUIDE.md - Comprehensive templating guide")
    print("   • .pre-commit-config.yaml - Code quality configuration")


if __name__ == "__main__":
    main()
