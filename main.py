#!/usr/bin/env python3
"""
Computer Vision CNC Manufacturing Platform - Main Application Entry Point
Testing version for Docker deployment
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis
import psycopg2
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Computer Vision CNC Manufacturing Platform",
    description="AI-powered quality control and manufacturing optimization platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://testuser:testpass123@localhost:5432/cv_cnc_manufacturing_test")
REDIS_URL = os.getenv("REDIS_URL", "redis://:testredis123@localhost:6379/0")
SERVICE_TYPE = os.getenv("CV_CNC_SERVICE_TYPE", "api")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting CV CNC Manufacturing Platform - {SERVICE_TYPE} service")
    
    # Test database connection
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
    
    # Test Redis connection
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Computer Vision CNC Manufacturing Platform",
        "service": SERVICE_TYPE,
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": SERVICE_TYPE,
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Check database
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@app.get("/api/status")
async def api_status():
    """API service status"""
    if SERVICE_TYPE != "api":
        raise HTTPException(status_code=404, detail="This endpoint is only available on API service")
    
    return {
        "service": "api",
        "endpoints": [
            "/",
            "/health",
            "/api/status",
            "/api/manufacturing/status",
            "/docs",
            "/redoc"
        ],
        "status": "ready"
    }

@app.get("/api/manufacturing/status")
async def manufacturing_status():
    """Manufacturing system status"""
    return {
        "cnc_machines": {
            "connected": 1,
            "active": 1,
            "total": 1
        },
        "computer_vision": {
            "status": "ready",
            "gpu_enabled": os.getenv("CV_CNC_USE_GPU", "false").lower() == "true",
            "models_loaded": 2
        },
        "quality_control": {
            "status": "active",
            "defect_detection": "enabled",
            "quality_threshold": 0.95
        },
        "production": {
            "mode": "test",
            "safety_enabled": False,
            "current_inspections": 0
        }
    }

@app.get("/vision/status")
async def vision_status():
    """Computer vision service status"""
    if SERVICE_TYPE != "vision":
        raise HTTPException(status_code=404, detail="This endpoint is only available on vision service")
    
    return {
        "service": "vision",
        "status": "ready",
        "gpu_enabled": os.getenv("CV_CNC_USE_GPU", "false").lower() == "true",
        "models": {
            "defect_detection": "loaded",
            "quality_control": "loaded"
        },
        "processing_queue": 0
    }

@app.get("/controller/status")
async def controller_status():
    """CNC controller service status"""
    if SERVICE_TYPE != "controller":
        raise HTTPException(status_code=404, detail="This endpoint is only available on controller service")
    
    return {
        "service": "controller",
        "status": "ready",
        "protocols": {
            "mtconnect": "connected",
            "opcua": "ready",
            "modbus": "ready"
        },
        "machines": {
            "cnc-001": {
                "status": "active",
                "spindle_speed": 1500,
                "execution": "ACTIVE"
            }
        }
    }

# Mock CNC data endpoint
@app.get("/api/cnc/machines")
async def get_cnc_machines():
    """Get CNC machine status"""
    return {
        "machines": [
            {
                "id": "cnc-001",
                "name": "Test CNC Machine",
                "status": "active",
                "type": "mill",
                "capabilities": ["drilling", "milling", "turning"],
                "current_job": {
                    "id": "job-001",
                    "part": "test-part-001",
                    "progress": 75,
                    "estimated_completion": "2025-08-02T23:30:00Z"
                },
                "metrics": {
                    "spindle_speed": 1500,
                    "feed_rate": 100,
                    "tool_wear": 0.2,
                    "temperature": 45.5
                }
            }
        ]
    }

# Mock computer vision endpoint
@app.get("/api/vision/models")
async def get_vision_models():
    """Get computer vision model status"""
    return {
        "models": [
            {
                "id": "defect-detection-v1",
                "name": "Defect Detection Model",
                "type": "YOLO",
                "version": "1.0",
                "status": "loaded",
                "accuracy": 0.94,
                "classes": ["crack", "scratch", "dent", "discoloration"]
            },
            {
                "id": "quality-control-v1",
                "name": "Quality Control Model",
                "type": "ResNet",
                "version": "1.0",
                "status": "loaded",
                "accuracy": 0.97,
                "classes": ["pass", "fail"]
            }
        ]
    }

def main():
    """Main entry point"""
    port = int(os.getenv("CV_CNC_API_PORT", "8000"))
    host = os.getenv("CV_CNC_API_HOST", "0.0.0.0")
    
    logger.info(f"Starting {SERVICE_TYPE} service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("CV_CNC_DEBUG", "false").lower() == "true",
        log_level="info"
    )

if __name__ == "__main__":
    main()
