"""
Development environment setup and configuration for Computer Vision CNC Manufacturing Platform.

This module provides development tools, configuration management, and environment
validation for the manufacturing platform.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

from ..core.base import BaseManufacturingComponent, OperationResult


class DevelopmentEnvironment(BaseManufacturingComponent):
    """Development environment management and validation."""
    
    def __init__(self, component_id: str = "dev_environment", config: Optional[Dict[str, Any]] = None):
        super().__init__(component_id, "DevelopmentEnvironment", config)
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
    async def initialize(self) -> OperationResult[bool]:
        """Initialize development environment."""
        try:
            validation_result = await self.validate_environment()
            if not validation_result.success:
                return validation_result
            
            setup_result = await self.setup_development_tools()
            if not setup_result.success:
                return setup_result
            
            self.logger.info("Development environment initialized successfully")
            return OperationResult.success_result(True)
            
        except Exception as e:
            return OperationResult.error_result(
                f"Failed to initialize development environment: {str(e)}",
                error_code="INITIALIZATION_ERROR"
            )
    
    async def validate_environment(self) -> OperationResult[Dict[str, Any]]:
        """Validate the development environment."""
        validation_results = {
            "python_version": self.python_version,
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "project_root": str(self.project_root),
            "checks": {}
        }
        
        # Check Python version
        min_python = (3, 8)
        current_python = (sys.version_info.major, sys.version_info.minor)
        
        if current_python >= min_python:
            validation_results["checks"]["python_version"] = {
                "status": "PASS",
                "message": f"Python {self.python_version} meets minimum requirement {min_python[0]}.{min_python[1]}"
            }
        else:
            validation_results["checks"]["python_version"] = {
                "status": "FAIL",
                "message": f"Python {self.python_version} below minimum requirement {min_python[0]}.{min_python[1]}"
            }
        
        # Check required directories
        required_dirs = [
            "src",
            "tests",
            "docs",
            "configs",
            "scripts",
            "docker"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                validation_results["checks"][f"directory_{dir_name}"] = {
                    "status": "PASS",
                    "message": f"Directory {dir_name} exists"
                }
            else:
                validation_results["checks"][f"directory_{dir_name}"] = {
                    "status": "FAIL",
                    "message": f"Directory {dir_name} missing"
                }
        
        # Check required files
        required_files = [
            "pyproject.toml",
            "requirements.txt",
            "requirements-dev.txt",
            "Dockerfile",
            "docker-compose.yml",
            "Makefile",
            ".gitignore",
            "README.md"
        ]
        
        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                validation_results["checks"][f"file_{file_name}"] = {
                    "status": "PASS",
                    "message": f"File {file_name} exists"
                }
            else:
                validation_results["checks"][f"file_{file_name}"] = {
                    "status": "FAIL",
                    "message": f"File {file_name} missing"
                }
        
        # Check system dependencies
        system_deps = ["git", "docker"]
        
        for dep in system_deps:
            try:
                result = subprocess.run([dep, "--version"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    validation_results["checks"][f"system_{dep}"] = {
                        "status": "PASS",
                        "message": f"{dep} is available",
                        "version": result.stdout.strip().split('\n')[0]
                    }
                else:
                    validation_results["checks"][f"system_{dep}"] = {
                        "status": "FAIL",
                        "message": f"{dep} command failed"
                    }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                validation_results["checks"][f"system_{dep}"] = {
                    "status": "FAIL",
                    "message": f"{dep} not found"
                }
        
        # Check optional dependencies
        optional_deps = ["nvidia-smi", "openssl"]
        
        for dep in optional_deps:
            try:
                result = subprocess.run([dep, "--version"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    validation_results["checks"][f"optional_{dep}"] = {
                        "status": "PASS",
                        "message": f"{dep} is available",
                        "version": result.stdout.strip().split('\n')[0]
                    }
                else:
                    validation_results["checks"][f"optional_{dep}"] = {
                        "status": "WARNING",
                        "message": f"{dep} command failed (optional)"
                    }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                validation_results["checks"][f"optional_{dep}"] = {
                    "status": "WARNING",
                    "message": f"{dep} not found (optional)"
                }
        
        # Overall validation status
        failed_checks = [k for k, v in validation_results["checks"].items() 
                        if v["status"] == "FAIL"]
        
        if failed_checks:
            validation_results["overall_status"] = "FAIL"
            validation_results["failed_checks"] = failed_checks
        else:
            validation_results["overall_status"] = "PASS"
        
        return OperationResult.success_result(validation_results)
    
    async def setup_development_tools(self) -> OperationResult[bool]:
        """Setup development tools and configurations."""
        try:
            # Ensure .vscode directory exists
            vscode_dir = self.project_root / ".vscode"
            vscode_dir.mkdir(exist_ok=True)
            
            # Create VS Code settings
            await self._create_vscode_settings(vscode_dir)
            
            # Create VS Code launch configuration
            await self._create_vscode_launch_config(vscode_dir)
            
            # Create development scripts
            await self._create_development_scripts()
            
            # Setup pre-commit hooks if git is available
            await self._setup_precommit_hooks()
            
            return OperationResult.success_result(True)
            
        except Exception as e:
            return OperationResult.error_result(
                f"Failed to setup development tools: {str(e)}",
                error_code="SETUP_ERROR"
            )
    
    async def _create_vscode_settings(self, vscode_dir: Path) -> None:
        """Create VS Code settings.json."""
        settings = {
            "python.defaultInterpreterPath": "./venv/bin/python" if platform.system() != "Windows" else ".\\venv\\Scripts\\python.exe",
            "python.linting.enabled": True,
            "python.linting.pylintEnabled": False,
            "python.linting.flake8Enabled": True,
            "python.linting.mypyEnabled": True,
            "python.formatting.provider": "black",
            "python.sortImports.args": ["--profile", "black"],
            "python.testing.pytestEnabled": True,
            "python.testing.unittestEnabled": False,
            "python.testing.pytestArgs": [
                "tests"
            ],
            "files.exclude": {
                "**/__pycache__": True,
                "**/.pytest_cache": True,
                "**/node_modules": True,
                "**/.mypy_cache": True,
                "**/site": True
            },
            "editor.formatOnSave": True,
            "editor.codeActionsOnSave": {
                "source.organizeImports": True
            },
            "docker.enableDockerBuildKit": True,
            "yaml.schemas": {
                "https://json.schemastore.org/github-workflow.json": ".github/workflows/*.yml"
            }
        }
        
        settings_file = vscode_dir / "settings.json"
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
    
    async def _create_vscode_launch_config(self, vscode_dir: Path) -> None:
        """Create VS Code launch.json for debugging."""
        launch_config = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Python: Current File",
                    "type": "python",
                    "request": "launch",
                    "program": "${file}",
                    "console": "integratedTerminal",
                    "justMyCode": True
                },
                {
                    "name": "Python: API Server",
                    "type": "python",
                    "request": "launch",
                    "module": "cv_cnc_manufacturing.api",
                    "console": "integratedTerminal",
                    "justMyCode": True,
                    "env": {
                        "PYTHONPATH": "${workspaceFolder}/src"
                    }
                },
                {
                    "name": "Python: Tests",
                    "type": "python",
                    "request": "launch",
                    "module": "pytest",
                    "args": [
                        "tests/",
                        "-v"
                    ],
                    "console": "integratedTerminal",
                    "justMyCode": True,
                    "env": {
                        "PYTHONPATH": "${workspaceFolder}/src"
                    }
                },
                {
                    "name": "Docker: Build and Debug",
                    "type": "docker",
                    "request": "launch",
                    "preLaunchTask": "docker-build",
                    "python": {
                        "pathMappings": [
                            {
                                "localRoot": "${workspaceFolder}",
                                "remoteRoot": "/app"
                            }
                        ],
                        "projectType": "fastapi"
                    }
                }
            ]
        }
        
        launch_file = vscode_dir / "launch.json"
        with open(launch_file, 'w') as f:
            json.dump(launch_config, f, indent=2)
    
    async def _create_development_scripts(self) -> None:
        """Create development utility scripts."""
        scripts_dir = self.project_root / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        # Create environment setup script
        if platform.system() == "Windows":
            setup_script = scripts_dir / "setup-dev.bat"
            setup_content = """@echo off
echo Setting up development environment...

REM Create virtual environment
python -m venv venv
call venv\\Scripts\\activate

REM Upgrade pip
python -m pip install --upgrade pip

REM Install development dependencies
pip install -r requirements-dev.txt
pip install -r requirements.txt

REM Install package in development mode
pip install -e .

REM Setup pre-commit hooks
pre-commit install

echo Development environment setup complete!
echo Activate with: venv\\Scripts\\activate
"""
        else:
            setup_script = scripts_dir / "setup-dev.sh"
            setup_content = """#!/bin/bash
echo "Setting up development environment..."

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install development dependencies
pip install -r requirements-dev.txt
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Setup pre-commit hooks
pre-commit install

echo "Development environment setup complete!"
echo "Activate with: source venv/bin/activate"
"""
            # Make script executable
            os.chmod(setup_script, 0o755)
        
        with open(setup_script, 'w') as f:
            f.write(setup_content)
        
        # Create testing script
        if platform.system() == "Windows":
            test_script = scripts_dir / "run-tests.bat"
            test_content = """@echo off
echo Running comprehensive tests...

REM Run unit tests
echo Running unit tests...
python -m pytest tests/unit/ -v --tb=short

REM Run integration tests
echo Running integration tests...
python -m pytest tests/integration/ -v --tb=short

REM Run code quality checks
echo Running code quality checks...
black --check src/ tests/
isort --check-only src/ tests/
flake8 src/ tests/
mypy src/

echo All tests completed!
"""
        else:
            test_script = scripts_dir / "run-tests.sh"
            test_content = """#!/bin/bash
echo "Running comprehensive tests..."

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v --tb=short

# Run integration tests
echo "Running integration tests..."
python -m pytest tests/integration/ -v --tb=short

# Run code quality checks
echo "Running code quality checks..."
black --check src/ tests/
isort --check-only src/ tests/
flake8 src/ tests/
mypy src/

echo "All tests completed!"
"""
            os.chmod(test_script, 0o755)
        
        with open(test_script, 'w') as f:
            f.write(test_content)
    
    async def _setup_precommit_hooks(self) -> None:
        """Setup pre-commit hooks if git is available."""
        try:
            git_dir = self.project_root / ".git"
            if git_dir.exists():
                # Check if pre-commit is available
                result = subprocess.run(
                    ["pre-commit", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    # Install pre-commit hooks
                    subprocess.run(
                        ["pre-commit", "install"],
                        cwd=self.project_root,
                        timeout=30
                    )
                    self.logger.info("Pre-commit hooks installed")
                else:
                    self.logger.warning("pre-commit not available, skipping hook installation")
        except Exception as e:
            self.logger.warning(f"Failed to setup pre-commit hooks: {str(e)}")
    
    async def create_feature_branch(self, feature_name: str) -> OperationResult[str]:
        """Create a new feature branch for development."""
        try:
            # Sanitize feature name
            branch_name = f"feature/{feature_name.replace(' ', '-').lower()}"
            
            # Create and checkout branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return OperationResult.success_result(
                    branch_name,
                    metadata={"message": f"Feature branch '{branch_name}' created"}
                )
            else:
                return OperationResult.error_result(
                    f"Failed to create branch: {result.stderr}",
                    error_code="GIT_ERROR"
                )
                
        except Exception as e:
            return OperationResult.error_result(
                f"Error creating feature branch: {str(e)}",
                error_code="BRANCH_CREATION_ERROR"
            )
    
    async def run_quality_checks(self) -> OperationResult[Dict[str, Any]]:
        """Run code quality checks."""
        checks = {}
        
        try:
            # Run black formatting check
            result = subprocess.run(
                ["black", "--check", "src/", "tests/"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            checks["black"] = {
                "passed": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
            
            # Run isort import sorting check
            result = subprocess.run(
                ["isort", "--check-only", "src/", "tests/"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            checks["isort"] = {
                "passed": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
            
            # Run flake8 linting
            result = subprocess.run(
                ["flake8", "src/", "tests/"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            checks["flake8"] = {
                "passed": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
            
            # Run mypy type checking
            result = subprocess.run(
                ["mypy", "src/"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            checks["mypy"] = {
                "passed": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
            
            # Overall result
            all_passed = all(check["passed"] for check in checks.values())
            
            return OperationResult.success_result(
                {
                    "all_passed": all_passed,
                    "checks": checks
                }
            )
            
        except Exception as e:
            return OperationResult.error_result(
                f"Error running quality checks: {str(e)}",
                error_code="QUALITY_CHECK_ERROR"
            )
    
    async def generate_documentation(self) -> OperationResult[bool]:
        """Generate project documentation."""
        try:
            # Build MkDocs documentation
            result = subprocess.run(
                ["python", "-m", "mkdocs", "build"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return OperationResult.success_result(
                    True,
                    metadata={"message": "Documentation generated successfully"}
                )
            else:
                return OperationResult.error_result(
                    f"Documentation build failed: {result.stderr}",
                    error_code="DOC_BUILD_ERROR"
                )
                
        except Exception as e:
            return OperationResult.error_result(
                f"Error generating documentation: {str(e)}",
                error_code="DOC_GENERATION_ERROR"
            )
    
    async def shutdown(self) -> OperationResult[bool]:
        """Shutdown development environment."""
        return OperationResult.success_result(True)


# Convenience functions for development
def validate_dev_environment() -> Dict[str, Any]:
    """Quick validation of development environment."""
    import asyncio
    
    async def _validate():
        dev_env = DevelopmentEnvironment()
        await dev_env.initialize()
        result = await dev_env.validate_environment()
        return result.result if result.success else {"error": result.error}
    
    return asyncio.run(_validate())


def setup_development_environment() -> bool:
    """Setup complete development environment."""
    import asyncio
    
    async def _setup():
        dev_env = DevelopmentEnvironment()
        result = await dev_env.initialize()
        return result.success
    
    return asyncio.run(_setup())


# Export public interface
__all__ = [
    'DevelopmentEnvironment',
    'validate_dev_environment',
    'setup_development_environment'
]
