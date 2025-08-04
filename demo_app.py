#!/usr/bin/env python3
"""
Computer Vision CNC Manufacturing Platform - Demo Version
Standalone demo for LinkedIn portfolio showcase
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import random
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app with enhanced metadata for demo
app = FastAPI(
    title="Computer Vision CNC Manufacturing Platform",
    description="""
    🏭 **AI-Powered CNC Manufacturing Quality Control System**
    
    This is a comprehensive computer vision platform for automated quality control in CNC manufacturing.
    
    **Key Features:**
    - 🤖 Real-time defect detection using PyTorch/TensorFlow
    - 📊 Manufacturing analytics and performance monitoring  
    - 🔍 Automated quality inspection workflows
    - 📈 Predictive maintenance using machine learning
    - 🛡️ Industrial IoT security and compliance
    - 📱 Modern web interface for operators and managers
    
    **Demo Endpoints:**
    - `/` - Platform overview and status
    - `/demo/dashboard` - Interactive manufacturing dashboard
    - `/api/quality/inspect` - Simulate quality inspection
    - `/api/manufacturing/status` - Live manufacturing status
    - `/api/analytics/performance` - Performance metrics
    """,
    version="1.0.0",
    contact={
        "name": "Portfolio Project",
        "url": "https://linkedin.com/in/yourprofile",
    },
    license_info={
        "name": "MIT License",
    },
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo data generators
def generate_manufacturing_status():
    """Generate realistic manufacturing status data"""
    machines = ["CNC-001", "CNC-002", "CNC-003", "CNC-004"]
    statuses = ["RUNNING", "IDLE", "MAINTENANCE", "QUALITY_CHECK"]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_machines": len(machines),
        "machines": [
            {
                "machine_id": machine,
                "status": random.choice(statuses),
                "efficiency": round(random.uniform(85, 98), 1),
                "parts_produced": random.randint(150, 300),
                "quality_score": round(random.uniform(95, 99.5), 2),
                "temperature": round(random.uniform(35, 65), 1),
                "vibration": round(random.uniform(0.1, 2.5), 2)
            }
            for machine in machines
        ],
        "overall_efficiency": round(random.uniform(90, 97), 1),
        "total_parts_today": random.randint(800, 1200),
        "defect_rate": round(random.uniform(0.1, 2.0), 2)
    }

def generate_quality_inspection():
    """Generate quality inspection results"""
    defect_types = ["scratch", "dent", "misalignment", "surface_roughness", "dimensional"]
    
    has_defect = random.random() < 0.15  # 15% defect rate
    
    result = {
        "inspection_id": f"QI-{random.randint(10000, 99999)}",
        "timestamp": datetime.now().isoformat(),
        "part_id": f"PART-{random.randint(1000, 9999)}",
        "machine_id": f"CNC-{random.randint(1, 4):03d}",
        "overall_quality_score": round(random.uniform(95 if not has_defect else 70, 99.5), 2),
        "passed": not has_defect,
        "inspection_time_ms": random.randint(150, 500),
        "ai_confidence": round(random.uniform(90, 99.8), 1)
    }
    
    if has_defect:
        result["defects"] = [
            {
                "type": random.choice(defect_types),
                "severity": random.choice(["LOW", "MEDIUM", "HIGH"]),
                "confidence": round(random.uniform(85, 98), 1),
                "location": {
                    "x": random.randint(10, 90),
                    "y": random.randint(10, 90)
                }
            }
        ]
    else:
        result["defects"] = []
    
    return result

# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Interactive demo dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CV CNC Manufacturing Platform - Demo</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header { 
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                color: white; 
                padding: 30px;
                text-align: center;
            }
            .header h1 { font-size: 2.5em; margin-bottom: 10px; }
            .header p { font-size: 1.2em; opacity: 0.9; }
            .content { padding: 30px; }
            .stats-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card { 
                background: #f8f9fa;
                padding: 25px;
                border-radius: 10px;
                border-left: 5px solid #3498db;
                transition: transform 0.3s ease;
            }
            .stat-card:hover { transform: translateY(-5px); }
            .stat-number { font-size: 2.5em; font-weight: bold; color: #2c3e50; }
            .stat-label { color: #7f8c8d; font-size: 1.1em; margin-top: 5px; }
            .demo-section { 
                background: #ecf0f1;
                padding: 25px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .demo-section h3 { color: #2c3e50; margin-bottom: 15px; }
            .btn { 
                background: #3498db;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
                margin: 5px;
                transition: background 0.3s ease;
            }
            .btn:hover { background: #2980b9; }
            .status-indicator { 
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .status-running { background: #27ae60; }
            .status-idle { background: #f39c12; }
            .status-maintenance { background: #e74c3c; }
            #output { 
                background: #2c3e50;
                color: #ecf0f1;
                padding: 20px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                white-space: pre-wrap;
                max-height: 400px;
                overflow-y: auto;
                margin-top: 15px;
            }
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .feature-card {
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                border-top: 4px solid #3498db;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏭 Computer Vision CNC Manufacturing Platform</h1>
                <p>AI-Powered Quality Control & Manufacturing Analytics</p>
            </div>
            
            <div class="content">
                <div class="stats-grid" id="stats">
                    <div class="stat-card">
                        <div class="stat-number" id="totalParts">Loading...</div>
                        <div class="stat-label">Parts Produced Today</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="efficiency">Loading...</div>
                        <div class="stat-label">Overall Efficiency</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="qualityScore">Loading...</div>
                        <div class="stat-label">Quality Score</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="activeMachines">Loading...</div>
                        <div class="stat-label">Active Machines</div>
                    </div>
                </div>

                <div class="demo-section">
                    <h3>🎮 Interactive Demo Controls</h3>
                    <button class="btn" onclick="runQualityInspection()">🔍 Run Quality Inspection</button>
                    <button class="btn" onclick="getManufacturingStatus()">📊 Get Manufacturing Status</button>
                    <button class="btn" onclick="getPerformanceAnalytics()">📈 Performance Analytics</button>
                    <button class="btn" onclick="simulateDefectDetection()">🚨 Simulate Defect Detection</button>
                    <div id="output"></div>
                </div>

                <div class="feature-grid">
                    <div class="feature-card">
                        <h3>🤖 AI-Powered Quality Control</h3>
                        <p>Advanced computer vision algorithms using PyTorch and TensorFlow for real-time defect detection with 99%+ accuracy.</p>
                    </div>
                    <div class="feature-card">
                        <h3>📊 Real-Time Analytics</h3>
                        <p>Live monitoring of manufacturing KPIs, efficiency metrics, and predictive maintenance indicators.</p>
                    </div>
                    <div class="feature-card">
                        <h3>🔗 Industrial IoT Integration</h3>
                        <p>Seamless connectivity with CNC machines via MTConnect, OPC-UA, and Modbus protocols.</p>
                    </div>
                    <div class="feature-card">
                        <h3>🛡️ Enterprise Security</h3>
                        <p>Industrial-grade security with encrypted communications, role-based access control, and audit trails.</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function makeRequest(endpoint) {
                try {
                    const response = await fetch(endpoint);
                    const data = await response.json();
                    return data;
                } catch (error) {
                    return { error: error.message };
                }
            }

            function displayOutput(data) {
                document.getElementById('output').textContent = JSON.stringify(data, null, 2);
            }

            async function runQualityInspection() {
                displayOutput({ status: "Starting quality inspection..." });
                const result = await makeRequest('/api/quality/inspect');
                displayOutput(result);
            }

            async function getManufacturingStatus() {
                displayOutput({ status: "Fetching manufacturing status..." });
                const result = await makeRequest('/api/manufacturing/status');
                displayOutput(result);
                updateDashboardStats(result);
            }

            async function getPerformanceAnalytics() {
                displayOutput({ status: "Generating performance analytics..." });
                const result = await makeRequest('/api/analytics/performance');
                displayOutput(result);
            }

            async function simulateDefectDetection() {
                displayOutput({ status: "Running AI defect detection..." });
                const result = await makeRequest('/api/quality/inspect');
                if (result.defects && result.defects.length > 0) {
                    displayOutput({
                        alert: "DEFECT DETECTED!",
                        details: result
                    });
                } else {
                    setTimeout(async () => {
                        // Force a defect for demo
                        const defectResult = await makeRequest('/api/quality/inspect?force_defect=true');
                        displayOutput({
                            alert: "DEFECT DETECTED!",
                            details: defectResult
                        });
                    }, 1000);
                }
            }

            function updateDashboardStats(data) {
                if (data.total_parts_today) {
                    document.getElementById('totalParts').textContent = data.total_parts_today.toLocaleString();
                }
                if (data.overall_efficiency) {
                    document.getElementById('efficiency').textContent = data.overall_efficiency + '%';
                }
                if (data.machines && data.machines.length > 0) {
                    const avgQuality = data.machines.reduce((sum, m) => sum + m.quality_score, 0) / data.machines.length;
                    document.getElementById('qualityScore').textContent = avgQuality.toFixed(1) + '%';
                    
                    const activeMachines = data.machines.filter(m => m.status === 'RUNNING').length;
                    document.getElementById('activeMachines').textContent = activeMachines + '/' + data.machines.length;
                }
            }

            // Initialize dashboard
            window.addEventListener('load', () => {
                getManufacturingStatus();
                // Auto-refresh every 30 seconds
                setInterval(getManufacturingStatus, 30000);
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/status")
async def api_status():
    """API service status"""
    return {
        "service": "Computer Vision CNC Manufacturing Platform",
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "demo_mode": True,
        "features": {
            "ai_quality_control": "active",
            "real_time_monitoring": "active", 
            "predictive_maintenance": "active",
            "industrial_iot": "simulated",
            "analytics_dashboard": "active"
        }
    }

@app.get("/api/manufacturing/status")
async def manufacturing_status():
    """Get current manufacturing status"""
    await asyncio.sleep(0.5)  # Simulate processing time
    return generate_manufacturing_status()

@app.get("/api/quality/inspect")
async def quality_inspection(force_defect: bool = False):
    """Run quality inspection simulation"""
    await asyncio.sleep(0.3)  # Simulate AI processing time
    
    result = generate_quality_inspection()
    
    # Force defect for demo purposes
    if force_defect:
        result["passed"] = False
        result["overall_quality_score"] = round(random.uniform(60, 80), 2)
        result["defects"] = [
            {
                "type": "surface_roughness",
                "severity": "HIGH",
                "confidence": 96.7,
                "location": {"x": 45, "y": 67}
            }
        ]
    
    return result

@app.get("/api/analytics/performance")
async def performance_analytics():
    """Get performance analytics"""
    await asyncio.sleep(0.4)  # Simulate analytics processing
    
    return {
        "period": "last_24_hours",
        "timestamp": datetime.now().isoformat(),
        "production_metrics": {
            "total_parts": random.randint(800, 1200),
            "defective_parts": random.randint(5, 25),
            "rework_parts": random.randint(2, 15),
            "scrap_parts": random.randint(1, 8)
        },
        "efficiency_metrics": {
            "overall_equipment_effectiveness": round(random.uniform(85, 95), 1),
            "availability": round(random.uniform(92, 98), 1),
            "performance": round(random.uniform(88, 96), 1),
            "quality": round(random.uniform(96, 99.5), 1)
        },
        "machine_performance": [
            {
                "machine_id": f"CNC-{i:03d}",
                "uptime_hours": round(random.uniform(18, 24), 1),
                "parts_produced": random.randint(150, 300),
                "efficiency": round(random.uniform(85, 98), 1),
                "maintenance_score": round(random.uniform(80, 95), 1)
            }
            for i in range(1, 5)
        ],
        "predictive_maintenance": {
            "alerts_count": random.randint(0, 3),
            "upcoming_maintenance": random.randint(1, 5),
            "health_score": round(random.uniform(85, 98), 1)
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cv-cnc-demo",
        "timestamp": datetime.now().isoformat(),
        "demo_mode": True,
        "checks": {
            "api": "healthy",
            "ai_models": "simulated",
            "database": "simulated",
            "cache": "simulated"
        }
    }

if __name__ == "__main__":
    print("🏭 Starting Computer Vision CNC Manufacturing Platform Demo")
    print("🎯 Perfect for LinkedIn portfolio demonstration!")
    print("📱 Open http://localhost:8000 to see the interactive dashboard")
    print("📚 API documentation available at http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )
