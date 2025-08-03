#!/usr/bin/env python3
"""
Simple test runner for the CV CNC Manufacturing Platform
This script runs a minimal version of the API for testing
"""

import os
import sys
import subprocess
import time

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "fastapi", "uvicorn", "psycopg2-binary", "redis", "requests"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def test_connections():
    """Test database connections"""
    print("\nTesting connections...")
    
    # Test PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="cv_cnc_manufacturing_test",
            user="testuser",
            password="testpass123"
        )
        conn.close()
        print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
    
    # Test Redis
    try:
        import redis
        r = redis.Redis(
            host="localhost",
            port=6379,
            password="testredis123",
            decode_responses=True
        )
        r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

def run_api():
    """Run the API server"""
    print("\nStarting API server...")
    print("API will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n🛑 API server stopped")

def main():
    """Main function"""
    print("🚀 CV CNC Manufacturing Platform - Test Setup")
    print("=" * 50)
    
    if not install_dependencies():
        sys.exit(1)
    
    test_connections()
    
    print(f"\n📊 Service Status:")
    print(f"   API Server: http://localhost:8000")
    print(f"   PostgreSQL: localhost:5432")
    print(f"   Redis: localhost:6379")
    print(f"   Mock CNC: Not available (container issue)")
    
    # Ask user if they want to start the API
    response = input("\nStart the API server? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        run_api()
    else:
        print("✅ Test setup complete. You can manually run 'python main.py' to start the API.")

if __name__ == "__main__":
    main()
