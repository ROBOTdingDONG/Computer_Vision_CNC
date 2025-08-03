#!/usr/bin/env python3
"""
Test suite for the CV CNC Manufacturing Platform API
Run with: python -m pytest test_api.py -v
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class TestAPI:
    """Test class for API endpoints"""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test the root endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Computer Vision CNC Manufacturing Platform"
            assert data["service"] == "api"
            assert data["version"] == "1.0.0"
            assert data["status"] == "running"
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test the health check endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "api"
            assert "checks" in data
            assert data["checks"]["database"] == "healthy"
            assert data["checks"]["redis"] == "healthy"

    @pytest.mark.asyncio
    async def test_api_status_endpoint(self):
        """Test the API status endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/status")
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "api"
            assert data["status"] == "ready"
            assert "endpoints" in data
            assert isinstance(data["endpoints"], list)

    @pytest.mark.asyncio
    async def test_manufacturing_status_endpoint(self):
        """Test the manufacturing status endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/manufacturing/status")
            assert response.status_code == 200
            data = response.json()
            
            # Check CNC machines
            assert "cnc_machines" in data
            cnc = data["cnc_machines"]
            assert cnc["connected"] == 1
            assert cnc["active"] == 1
            assert cnc["total"] == 1
            
            # Check computer vision
            assert "computer_vision" in data
            cv = data["computer_vision"]
            assert cv["status"] == "ready"
            assert cv["gpu_enabled"] is False
            assert cv["models_loaded"] == 2
            
            # Check quality control
            assert "quality_control" in data
            qc = data["quality_control"]
            assert qc["status"] == "active"
            assert qc["defect_detection"] == "enabled"
            assert qc["quality_threshold"] == 0.95
            
            # Check production
            assert "production" in data
            prod = data["production"]
            assert prod["mode"] == "test"
            assert prod["safety_enabled"] is False

    @pytest.mark.asyncio
    async def test_cnc_machines_endpoint(self):
        """Test the CNC machines endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/cnc/machines")
            assert response.status_code == 200
            data = response.json()
            assert "machines" in data
            machines = data["machines"]
            assert len(machines) == 1
            
            machine = machines[0]
            assert machine["id"] == "cnc-001"
            assert machine["name"] == "Test CNC Machine"
            assert machine["status"] == "active"
            assert machine["type"] == "mill"
            assert "capabilities" in machine
            assert "current_job" in machine
            assert "metrics" in machine

    @pytest.mark.asyncio
    async def test_vision_models_endpoint(self):
        """Test the computer vision models endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/vision/models")
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            models = data["models"]
            assert len(models) == 2
            
            # Check defect detection model
            defect_model = next(m for m in models if m["id"] == "defect-detection-v1")
            assert defect_model["name"] == "Defect Detection Model"
            assert defect_model["type"] == "YOLO"
            assert defect_model["status"] == "loaded"
            assert defect_model["accuracy"] == 0.94
            
            # Check quality control model
            quality_model = next(m for m in models if m["id"] == "quality-control-v1")
            assert quality_model["name"] == "Quality Control Model"
            assert quality_model["type"] == "ResNet"
            assert quality_model["status"] == "loaded"
            assert quality_model["accuracy"] == 0.97

    @pytest.mark.asyncio
    async def test_nonexistent_endpoint(self):
        """Test that nonexistent endpoints return 404"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/nonexistent")
            assert response.status_code == 404

def test_sync_api_call():
    """Test synchronous API call for comparison"""
    import requests
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Computer Vision CNC Manufacturing Platform"

if __name__ == "__main__":
    print("🧪 Running API tests...")
    print("Make sure the API server is running: python main.py")
    print()
    
    # Run a quick connectivity test
    try:
        import requests
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            print("Run tests with: python -m pytest test_api.py -v")
        else:
            print(f"❌ API server returned status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("Make sure to start the server first: python main.py")
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
