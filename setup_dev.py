#!/usr/bin/env python3
"""
Computer Vision CNC Manufacturing Platform - Development Setup
This script sets up the development environment for testing and development
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    """Print setup header"""
    print("=" * 70)
    print("🚀 CV CNC Manufacturing Platform - Development Setup")
    print("=" * 70)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def create_venv():
    """Create virtual environment"""
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    print("📦 Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def get_activation_command():
    """Get the command to activate virtual environment"""
    if platform.system() == "Windows":
        return ".venv\\Scripts\\activate"
    else:
        return "source .venv/bin/activate"

def install_packages():
    """Install required packages"""
    print("📥 Installing packages...")
    
    # Determine the pip executable
    if platform.system() == "Windows":
        pip_exe = ".venv\\Scripts\\pip.exe"
    else:
        pip_exe = ".venv/bin/pip"
    
    try:
        # Upgrade pip first
        subprocess.run([pip_exe, "install", "--upgrade", "pip"], check=True)
        
        # Install minimal requirements
        subprocess.run([pip_exe, "install", "-r", "requirements-minimal.txt"], check=True)
        
        print("✅ Packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")
    
    # Determine the python executable
    if platform.system() == "Windows":
        python_exe = ".venv\\Scripts\\python.exe"
    else:
        python_exe = ".venv/bin/python"
    
    try:
        # Test imports
        test_script = """
import fastapi
import uvicorn
import psycopg2
import redis
import pydantic
print("✅ All essential packages imported successfully")
"""
        result = subprocess.run([python_exe, "-c", test_script], 
                              capture_output=True, text=True, check=True)
        print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Package test failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker available: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Docker not available (optional for development)")
        return False

def show_next_steps():
    """Show next steps to the user"""
    activation_cmd = get_activation_command()
    
    print("\n" + "=" * 70)
    print("🎉 Setup Complete!")
    print("=" * 70)
    print("\n📋 Next Steps:")
    print()
    print("1. Activate virtual environment:")
    print(f"   {activation_cmd}")
    print()
    print("2. Start Docker services (optional):")
    print("   docker-compose -f docker-compose.simple.yml up -d")
    print()
    print("3. Run the application:")
    print("   python main.py")
    print()
    print("4. Access the API:")
    print("   • API: http://localhost:8000")
    print("   • Documentation: http://localhost:8000/docs")
    print("   • Health Check: http://localhost:8000/health")
    print()
    print("5. Test endpoints:")
    print("   curl http://localhost:8000/api/manufacturing/status")
    print("   curl http://localhost:8000/api/cnc/machines")
    print("   curl http://localhost:8000/api/vision/models")
    print()

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_venv():
        sys.exit(1)
    
    # Install packages
    if not install_packages():
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        sys.exit(1)
    
    # Check Docker (optional)
    check_docker()
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()
