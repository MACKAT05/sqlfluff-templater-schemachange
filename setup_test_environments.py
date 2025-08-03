#!/usr/bin/env python3
"""
Multi-Python Environment Setup and Testing Script

This script:
1. Detects available Python versions on the system
2. Creates virtual environments for each Python version
3. Installs required packages (sqlfluff, schemachange, this package)
4. Runs comprehensive cross-functionality tests
5. Generates a test report
"""

import subprocess
import sys
import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PythonEnvironmentManager:
    """Manage multiple Python environments for testing."""
    
    def __init__(self, test_envs_dir: str = "test_envs"):
        self.test_envs_dir = Path(test_envs_dir)
        self.test_envs_dir.mkdir(exist_ok=True)
        self.temp_dir = Path("temp")
        self.results = {}
        
    def detect_python_versions(self) -> List[str]:
        """Detect available Python versions on the system."""
        versions = []
        
        # Common Python executable patterns
        python_patterns = [
            "python3.8", "python3.9", "python3.10", "python3.11", "python3.12",
            "python38", "python39", "python310", "python311", "python312"
        ]
        
        # Check system python
        try:
            result = subprocess.run([sys.executable, "--version"], 
                                  capture_output=True, text=True, check=True)
            current_version = result.stdout.strip().split()[1]
            versions.append((sys.executable, current_version))
            logger.info(f"Found current Python: {current_version}")
        except Exception as e:
            logger.warning(f"Could not get current Python version: {e}")
        
        # Check for other Python versions
        for pattern in python_patterns:
            try:
                result = subprocess.run([pattern, "--version"], 
                                      capture_output=True, text=True, check=True)
                version = result.stdout.strip().split()[1]
                executable = shutil.which(pattern)
                if executable and (executable, version) not in versions:
                    versions.append((executable, version))
                    logger.info(f"Found Python: {pattern} -> {version}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        # Check pyenv versions if available
        try:
            result = subprocess.run(["pyenv", "versions", "--bare"], 
                                  capture_output=True, text=True, check=True)
            for line in result.stdout.strip().split('\n'):
                if line and not line.startswith('system'):
                    try:
                        pyenv_python = subprocess.run(
                            ["pyenv", "which", "python"], 
                            env={**os.environ, "PYENV_VERSION": line},
                            capture_output=True, text=True, check=True
                        )
                        executable = pyenv_python.stdout.strip()
                        
                        version_result = subprocess.run(
                            [executable, "--version"],
                            capture_output=True, text=True, check=True
                        )
                        version = version_result.stdout.strip().split()[1]
                        
                        if (executable, version) not in versions:
                            versions.append((executable, version))
                            logger.info(f"Found pyenv Python: {line} -> {version}")
                    except Exception as e:
                        logger.debug(f"Could not check pyenv version {line}: {e}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.debug("pyenv not available")
        
        # Remove duplicates and sort by version
        unique_versions = list(set(versions))
        unique_versions.sort(key=lambda x: self._version_key(x[1]))
        
        logger.info(f"Total Python versions found: {len(unique_versions)}")
        return unique_versions
    
    def _version_key(self, version_str: str) -> Tuple[int, ...]:
        """Convert version string to tuple for sorting."""
        try:
            return tuple(map(int, version_str.split('.')[:3]))
        except:
            return (0, 0, 0)
    
    def create_virtual_environment(self, python_executable: str, version: str) -> Optional[Path]:
        """Create a virtual environment for the given Python version."""
        safe_version = version.replace('.', '_')
        venv_path = self.test_envs_dir / f"python_{safe_version}"
        
        try:
            if venv_path.exists():
                shutil.rmtree(venv_path)
            
            logger.info(f"Creating virtual environment for Python {version}")
            subprocess.run([python_executable, "-m", "venv", str(venv_path)], 
                         check=True, capture_output=True)
            
            # Get the correct Python executable in the venv
            if os.name == 'nt':  # Windows
                venv_python = venv_path / "Scripts" / "python.exe"
                pip_executable = venv_path / "Scripts" / "pip.exe"
            else:  # Unix-like
                venv_python = venv_path / "bin" / "python"
                pip_executable = venv_path / "bin" / "pip"
            
            # Upgrade pip
            subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            logger.info(f"✓ Created virtual environment: {venv_path}")
            return venv_path
            
        except Exception as e:
            logger.error(f"Failed to create virtual environment for Python {version}: {e}")
            return None
    
    def install_packages(self, venv_path: Path, version: str) -> bool:
        """Install required packages in the virtual environment."""
        if os.name == 'nt':  # Windows
            python_executable = venv_path / "Scripts" / "python.exe"
        else:  # Unix-like
            python_executable = venv_path / "bin" / "python"
        
        packages = [
            "sqlfluff>=2.0.0",
            "PyYAML>=5.1",
            "schemachange>=3.0.0",  # Install schemachange for comparison testing
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0"
        ]
        
        try:
            logger.info(f"Installing packages in Python {version} environment")
            
            # Install packages
            for package in packages:
                logger.info(f"  Installing {package}")
                subprocess.run([str(python_executable), "-m", "pip", "install", package], 
                             check=True, capture_output=True)
            
            # Install this package in development mode
            logger.info("  Installing this package in development mode")
            subprocess.run([str(python_executable), "-m", "pip", "install", "-e", "."], 
                         check=True, capture_output=True)
            
            logger.info(f"✓ Installed packages in Python {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install packages in Python {version}: {e}")
            return False
    
    def run_sqlfluff_tests(self, venv_path: Path, version: str) -> Dict:
        """Run SQLFluff tests on example files."""
        if os.name == 'nt':  # Windows
            python_executable = venv_path / "Scripts" / "python.exe"
            sqlfluff_executable = venv_path / "Scripts" / "sqlfluff.exe"
        else:  # Unix-like
            python_executable = venv_path / "bin" / "python"
            sqlfluff_executable = venv_path / "bin" / "sqlfluff"
        
        results = {
            "version": version,
            "sqlfluff_tests": [],
            "errors": [],
            "success": True
        }
        
        try:
            # Test examples directory
            if Path("examples").exists():
                logger.info(f"Running SQLFluff tests on examples (Python {version})")
                
                # Test basic linting
                try:
                    result = subprocess.run([
                        str(sqlfluff_executable), "lint", 
                        "examples/migrations/", "--dialect", "snowflake"
                    ], capture_output=True, text=True, timeout=120)
                    
                    results["sqlfluff_tests"].append({
                        "test": "examples_lint",
                        "returncode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    })
                    
                    if result.returncode != 0:
                        logger.warning(f"SQLFluff linting found issues in Python {version}")
                    else:
                        logger.info(f"✓ SQLFluff linting passed in Python {version}")
                        
                except subprocess.TimeoutExpired:
                    results["errors"].append("SQLFluff lint timed out")
                    results["success"] = False
                
                # Test rendering
                for sql_file in Path("examples/migrations").glob("*.sql"):
                    try:
                        result = subprocess.run([
                            str(sqlfluff_executable), "render", str(sql_file)
                        ], capture_output=True, text=True, timeout=60)
                        
                        results["sqlfluff_tests"].append({
                            "test": f"render_{sql_file.name}",
                            "returncode": result.returncode,
                            "stdout": result.stdout,
                            "stderr": result.stderr
                        })
                        
                        if result.returncode == 0:
                            logger.info(f"✓ Rendered {sql_file.name} in Python {version}")
                        else:
                            logger.warning(f"Failed to render {sql_file.name} in Python {version}")
                            
                    except subprocess.TimeoutExpired:
                        results["errors"].append(f"Rendering {sql_file.name} timed out")
            
            # Test temp directory if it exists
            if self.temp_dir.exists():
                logger.info(f"Running SQLFluff tests on temp examples (Python {version})")
                
                for test_dir in self.temp_dir.iterdir():
                    if test_dir.is_dir():
                        sql_files = list(test_dir.rglob("*.sql"))
                        if sql_files:
                            try:
                                result = subprocess.run([
                                    str(sqlfluff_executable), "lint", 
                                    str(test_dir), "--dialect", "snowflake"
                                ], capture_output=True, text=True, timeout=60)
                                
                                results["sqlfluff_tests"].append({
                                    "test": f"temp_{test_dir.name}_lint",
                                    "returncode": result.returncode,
                                    "stdout": result.stdout,
                                    "stderr": result.stderr
                                })
                                
                            except subprocess.TimeoutExpired:
                                results["errors"].append(f"Linting {test_dir.name} timed out")
                                
        except Exception as e:
            logger.error(f"Error running SQLFluff tests in Python {version}: {e}")
            results["errors"].append(str(e))
            results["success"] = False
        
        return results
    
    def run_schemachange_tests(self, venv_path: Path, version: str) -> Dict:
        """Run schemachange render tests for comparison."""
        if os.name == 'nt':  # Windows
            python_executable = venv_path / "Scripts" / "python.exe"
        else:  # Unix-like
            python_executable = venv_path / "bin" / "python"
        
        results = {
            "version": version,
            "schemachange_tests": [],
            "errors": [],
            "success": True
        }
        
        try:
            # Test schemachange render on examples
            if Path("examples").exists():
                logger.info(f"Running schemachange render tests (Python {version})")
                
                # Change to examples directory
                original_cwd = os.getcwd()
                os.chdir("examples")
                
                try:
                    for sql_file in Path("migrations").glob("*.sql"):
                        try:
                            result = subprocess.run([
                                str(python_executable), "-m", "schemachange", 
                                "render", str(sql_file),
                                "--config-folder", ".",
                                "--vars", json.dumps({"environment": "test"})
                            ], capture_output=True, text=True, timeout=60)
                            
                            results["schemachange_tests"].append({
                                "test": f"render_{sql_file.name}",
                                "returncode": result.returncode,
                                "stdout": result.stdout,
                                "stderr": result.stderr
                            })
                            
                            if result.returncode == 0:
                                logger.info(f"✓ Schemachange rendered {sql_file.name} in Python {version}")
                            else:
                                logger.warning(f"Schemachange failed to render {sql_file.name} in Python {version}")
                                
                        except subprocess.TimeoutExpired:
                            results["errors"].append(f"Schemachange rendering {sql_file.name} timed out")
                            
                finally:
                    os.chdir(original_cwd)
                    
        except Exception as e:
            logger.error(f"Error running schemachange tests in Python {version}: {e}")
            results["errors"].append(str(e))
            results["success"] = False
        
        return results
    
    def generate_test_report(self) -> str:
        """Generate a comprehensive test report."""
        report_lines = [
            "# SQLFluff Schemachange Templater - Cross-Platform Test Report",
            "",
            f"## Summary",
            f"- Total Python versions tested: {len(self.results)}",
            f"- Successful environments: {sum(1 for r in self.results.values() if r.get('overall_success', False))}",
            f"- Failed environments: {sum(1 for r in self.results.values() if not r.get('overall_success', False))}",
            ""
        ]
        
        for version, result in self.results.items():
            report_lines.extend([
                f"## Python {version}",
                f"- Overall Success: {'✓' if result.get('overall_success', False) else '✗'}",
                f"- Environment Created: {'✓' if result.get('env_created', False) else '✗'}",
                f"- Packages Installed: {'✓' if result.get('packages_installed', False) else '✗'}",
                ""
            ])
            
            if 'sqlfluff_results' in result:
                sqlfluff = result['sqlfluff_results']
                report_lines.extend([
                    "### SQLFluff Tests",
                    f"- Success: {'✓' if sqlfluff.get('success', False) else '✗'}",
                    f"- Tests Run: {len(sqlfluff.get('sqlfluff_tests', []))}",
                    f"- Errors: {len(sqlfluff.get('errors', []))}",
                    ""
                ])
                
                for test in sqlfluff.get('sqlfluff_tests', []):
                    status = "✓" if test['returncode'] == 0 else "✗"
                    report_lines.append(f"  - {test['test']}: {status}")
                
                if sqlfluff.get('errors'):
                    report_lines.extend(["", "#### Errors:"])
                    for error in sqlfluff['errors']:
                        report_lines.append(f"  - {error}")
                
                report_lines.append("")
            
            if 'schemachange_results' in result:
                schemachange = result['schemachange_results']
                report_lines.extend([
                    "### Schemachange Tests",
                    f"- Success: {'✓' if schemachange.get('success', False) else '✗'}",
                    f"- Tests Run: {len(schemachange.get('schemachange_tests', []))}",
                    f"- Errors: {len(schemachange.get('errors', []))}",
                    ""
                ])
                
                for test in schemachange.get('schemachange_tests', []):
                    status = "✓" if test['returncode'] == 0 else "✗"
                    report_lines.append(f"  - {test['test']}: {status}")
                
                if schemachange.get('errors'):
                    report_lines.extend(["", "#### Errors:"])
                    for error in schemachange['errors']:
                        report_lines.append(f"  - {error}")
                
                report_lines.append("")
            
            report_lines.append("---")
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def run_comprehensive_tests(self):
        """Run comprehensive tests across all Python versions."""
        logger.info("🚀 Starting comprehensive multi-Python testing")
        
        # Generate test files first
        logger.info("Generating test files...")
        try:
            subprocess.run([sys.executable, "test_generator.py"], check=True)
        except Exception as e:
            logger.error(f"Failed to generate test files: {e}")
            return
        
        # Detect Python versions
        python_versions = self.detect_python_versions()
        
        if not python_versions:
            logger.error("No Python versions found!")
            return
        
        logger.info(f"Testing with {len(python_versions)} Python versions")
        
        # Test each Python version
        for python_executable, version in python_versions:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing Python {version}")
            logger.info(f"{'='*60}")
            
            result = {
                "version": version,
                "executable": python_executable,
                "overall_success": False
            }
            
            # Create virtual environment
            venv_path = self.create_virtual_environment(python_executable, version)
            if venv_path:
                result["env_created"] = True
                
                # Install packages
                if self.install_packages(venv_path, version):
                    result["packages_installed"] = True
                    
                    # Run SQLFluff tests
                    logger.info(f"Running SQLFluff tests for Python {version}")
                    sqlfluff_results = self.run_sqlfluff_tests(venv_path, version)
                    result["sqlfluff_results"] = sqlfluff_results
                    
                    # Run schemachange tests
                    logger.info(f"Running schemachange tests for Python {version}")
                    schemachange_results = self.run_schemachange_tests(venv_path, version)
                    result["schemachange_results"] = schemachange_results
                    
                    # Determine overall success
                    result["overall_success"] = (
                        sqlfluff_results.get("success", False) and 
                        schemachange_results.get("success", False)
                    )
                else:
                    result["packages_installed"] = False
            else:
                result["env_created"] = False
            
            self.results[version] = result
        
        # Generate report
        report = self.generate_test_report()
        report_path = Path("test_report.md")
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"\n🎉 Testing complete! Report saved to {report_path}")
        
        # Print summary
        successful = sum(1 for r in self.results.values() if r.get('overall_success', False))
        total = len(self.results)
        
        logger.info(f"📊 Summary: {successful}/{total} Python versions passed all tests")
        
        if successful == total:
            logger.info("🎉 All tests passed! Package is ready for release.")
        else:
            logger.warning("⚠️  Some tests failed. Please review the report.")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        # Clean test environments
        if Path("test_envs").exists():
            shutil.rmtree("test_envs")
            logger.info("Cleaned test environments")
        if Path("temp").exists():
            shutil.rmtree("temp")
            logger.info("Cleaned temp directory")
        return
    
    manager = PythonEnvironmentManager()
    manager.run_comprehensive_tests()


if __name__ == "__main__":
    main()