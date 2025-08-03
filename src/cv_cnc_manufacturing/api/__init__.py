"""
REST API implementation for Computer Vision CNC Manufacturing Platform.

This module provides comprehensive RESTful API endpoints for manufacturing
operations, quality control, machine management, and real-time monitoring.

Safety Notice: API endpoints that control manufacturing equipment should
implement proper authentication, authorization, and safety validation.
"""

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

try:
    from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, validator
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    # Create minimal replacements when FastAPI is not available
    class FastAPI:
        def __init__(self, **kwargs): pass
        def get(self, *args, **kwargs): return lambda f: f
        def post(self, *args, **kwargs): return lambda f: f
        def put(self, *args, **kwargs): return lambda f: f
        def delete(self, *args, **kwargs): return lambda f: f
        def websocket(self, *args, **kwargs): return lambda f: f
        def add_middleware(self, *args, **kwargs): pass
    
    class HTTPException(Exception): pass
    class WebSocket: pass
    class HTTPBearer: 
        def __call__(self, *args, **kwargs): return None
    class HTTPAuthorizationCredentials: pass
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        def dict(self): return self.__dict__
    
    def Field(default=None, **kwargs): return default
    def Depends(*args, **kwargs): return lambda f: f
    def validator(*args, **kwargs): return lambda f: f
    
    uvicorn = None
    HAS_FASTAPI = False

from ..core.base import (
    BaseAsyncComponent,
    OperationResult,
    ComponentState,
    Priority,
    ManufacturingEvent
)
from ..computer_vision import QualityInspector, InspectionReport, InspectionResult
from ..cnc import CNCManager, MachineStatus, MachineState, CNCCommand


# API Configuration
@dataclass
class APIConfig:
    """Configuration for the Manufacturing API server."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    title: str = "Computer Vision CNC Manufacturing API"
    description: str = "Enterprise Computer Vision CNC Manufacturing Platform API"
    version: str = "1.0.0"
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


# API Models
class APIResponse(BaseModel):
    """Standard API response format."""
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str = Field(default_factory=lambda: str(uuid4()))


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    uptime_seconds: float
    components: Dict[str, str]
    timestamp: datetime


class InspectionRequest(BaseModel):
    """Request model for quality inspection."""
    part_id: str = Field(..., description="Unique part identifier")
    image_data: str = Field(..., description="Base64 encoded image data")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    @validator('part_id')
    def validate_part_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Part ID cannot be empty")
        return v.strip()


class InspectionResponse(BaseModel):
    """Response model for quality inspection."""
    part_id: str
    inspection_result: str
    overall_score: float
    defect_count: int
    processing_time_ms: float
    defects: List[Dict[str, Any]]
    measurements: List[Dict[str, Any]]
    timestamp: datetime


class MachineStatusResponse(BaseModel):
    """Response model for machine status."""
    machine_id: str
    state: str
    is_operational: bool
    program_name: Optional[str]
    feedrate: Optional[float]
    axis_positions: Dict[str, Any]
    alarms: List[str]
    timestamp: datetime


class CommandRequest(BaseModel):
    """Request model for machine commands."""
    command: str = Field(..., description="Command to execute")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Command parameters")
    safety_confirmation: bool = Field(default=False, description="Safety confirmation for critical commands")
    
    @validator('command')
    def validate_command(cls, v):
        valid_commands = [cmd.value for cmd in CNCCommand]
        if v not in valid_commands:
            raise ValueError(f"Invalid command. Must be one of: {valid_commands}")
        return v


class EventSubscription(BaseModel):
    """Event subscription configuration."""
    event_types: List[str] = Field(..., description="List of event types to subscribe to")
    priority_filter: Optional[str] = Field(default=None, description="Minimum priority level")
    component_filter: Optional[str] = Field(default=None, description="Filter by component")


# Security
security = HTTPBearer() if HTTPBearer else None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and validate user from JWT token."""
    # In a real implementation, this would validate JWT tokens
    # For now, we'll do basic validation
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Mock user validation
    return {"user_id": "user123", "permissions": ["read", "write", "admin"]}


def require_permission(permission: str):
    """Decorator to require specific permissions."""
    def decorator(user: dict = Depends(get_current_user)):
        if permission not in user.get("permissions", []):
            raise HTTPException(status_code=403, detail=f"Permission '{permission}' required")
        return user
    return decorator


# Main API Application
class ManufacturingAPI(BaseAsyncComponent):
    """Main API server for the manufacturing platform."""
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(component_id, "ManufacturingAPI", config)
        
        if FastAPI is None:
            raise ImportError("FastAPI not available. Install fastapi and uvicorn packages.")
        
        self.app = FastAPI(
            title="Computer Vision CNC Manufacturing Platform",
            description="Enterprise manufacturing platform with AI-powered quality control",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Configuration
        self.host = config.get('host', '0.0.0.0') if config else '0.0.0.0'
        self.port = config.get('port', 8000) if config else 8000
        self.workers = config.get('workers', 1) if config else 1
        
        # Components
        self.quality_inspector: Optional[QualityInspector] = None
        self.cnc_manager: Optional[CNCManager] = None
        
        # WebSocket connections for real-time updates
        self.websocket_connections: List[WebSocket] = []
        self.event_subscribers: Dict[str, EventSubscription] = {}
        
        # Server instance
        self.server = None
        
        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup FastAPI middleware."""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, restrict this
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Custom middleware for request logging
        @self.app.middleware("http")
        async def log_requests(request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            self.logger.info(
                "API request processed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time_seconds=process_time
            )
            return response
    
    def _setup_routes(self):
        """Setup API routes."""
        
        # Health check endpoint
        @self.app.get("/health", response_model=HealthCheckResponse)
        async def health_check():
            """Get system health status."""
            components = {
                "api": self.state.name,
                "quality_inspector": self.quality_inspector.state.name if self.quality_inspector else "NOT_INITIALIZED",
                "cnc_manager": self.cnc_manager.state.name if self.cnc_manager else "NOT_INITIALIZED"
            }
            
            return HealthCheckResponse(
                status="healthy" if self.is_healthy else "unhealthy",
                version="1.0.0",
                uptime_seconds=self.uptime_seconds,
                components=components,
                timestamp=datetime.now(timezone.utc)
            )
        
        # Root endpoint
        @self.app.get("/")
        async def root():
            """API root endpoint."""
            return APIResponse(
                success=True,
                message="Computer Vision CNC Manufacturing Platform API",
                data={
                    "version": "1.0.0",
                    "docs": "/docs",
                    "health": "/health"
                }
            )
        
        # Quality Control Endpoints
        @self.app.post("/api/v1/quality/inspect", response_model=InspectionResponse)
        async def quality_inspect(
            request: InspectionRequest,
            background_tasks: BackgroundTasks,
            user: dict = Depends(require_permission("quality_inspect"))
        ):
            """Perform quality inspection on a part."""
            if not self.quality_inspector:
                raise HTTPException(status_code=503, detail="Quality inspector not available")
            
            try:
                # Decode base64 image
                import base64
                import numpy as np
                import cv2
                
                image_bytes = base64.b64decode(request.image_data)
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is None:
                    raise HTTPException(status_code=400, detail="Invalid image data")
                
                # Perform inspection
                result = await self.quality_inspector.inspect_part(image, request.part_id)
                
                if not result.success:
                    raise HTTPException(status_code=500, detail=f"Inspection failed: {result.error}")
                
                report = result.result
                
                # Log inspection event
                background_tasks.add_task(
                    self._log_inspection_event,
                    report,
                    user["user_id"]
                )
                
                return InspectionResponse(
                    part_id=report.part_id,
                    inspection_result=report.inspection_result.name,
                    overall_score=report.overall_score,
                    defect_count=report.defect_count,
                    processing_time_ms=report.processing_time_ms,
                    defects=[self._defect_to_dict(d) for d in report.defects],
                    measurements=[self._measurement_to_dict(m) for m in report.measurements],
                    timestamp=report.inspection_timestamp
                )
                
            except Exception as e:
                self.logger.error(f"Quality inspection error: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        # Machine Management Endpoints
        @self.app.get("/api/v1/machines", response_model=Dict[str, MachineStatusResponse])
        async def get_all_machines(user: dict = Depends(require_permission("machine_read"))):
            """Get status of all machines."""
            if not self.cnc_manager:
                raise HTTPException(status_code=503, detail="CNC manager not available")
            
            result = await self.cnc_manager.get_all_status()
            if not result.success:
                raise HTTPException(status_code=500, detail=f"Failed to get machine status: {result.error}")
            
            response = {}
            for machine_id, status in result.result.items():
                response[machine_id] = self._status_to_response(status)
            
            return response
        
        @self.app.get("/api/v1/machines/{machine_id}", response_model=MachineStatusResponse)
        async def get_machine_status(
            machine_id: str,
            user: dict = Depends(require_permission("machine_read"))
        ):
            """Get status of a specific machine."""
            if not self.cnc_manager:
                raise HTTPException(status_code=503, detail="CNC manager not available")
            
            if machine_id not in self.cnc_manager.controllers:
                raise HTTPException(status_code=404, detail="Machine not found")
            
            controller = self.cnc_manager.controllers[machine_id]
            if not controller.current_status:
                raise HTTPException(status_code=503, detail="Machine status not available")
            
            return self._status_to_response(controller.current_status)
        
        @self.app.post("/api/v1/machines/{machine_id}/command")
        async def send_machine_command(
            machine_id: str,
            request: CommandRequest,
            user: dict = Depends(require_permission("machine_control"))
        ):
            """Send command to a specific machine."""
            if not self.cnc_manager:
                raise HTTPException(status_code=503, detail="CNC manager not available")
            
            if machine_id not in self.cnc_manager.controllers:
                raise HTTPException(status_code=404, detail="Machine not found")
            
            # Safety check for critical commands
            critical_commands = [CNCCommand.EMERGENCY_STOP.value, CNCCommand.START_PROGRAM.value]
            if request.command in critical_commands and not request.safety_confirmation:
                raise HTTPException(
                    status_code=400,
                    detail="Safety confirmation required for critical commands"
                )
            
            controller = self.cnc_manager.controllers[machine_id]
            command_enum = CNCCommand(request.command)
            
            result = await controller.send_command(command_enum, request.parameters)
            
            if not result.success:
                raise HTTPException(status_code=500, detail=f"Command failed: {result.error}")
            
            return APIResponse(
                success=True,
                message=f"Command '{request.command}' sent successfully",
                data={"machine_id": machine_id, "command": request.command}
            )
        
        @self.app.post("/api/v1/emergency-stop")
        async def emergency_stop_all(user: dict = Depends(require_permission("emergency_control"))):
            """Trigger emergency stop on all machines."""
            if not self.cnc_manager:
                raise HTTPException(status_code=503, detail="CNC manager not available")
            
            result = await self.cnc_manager.emergency_stop_all()
            
            return APIResponse(
                success=True,
                message="Emergency stop triggered on all machines",
                data=result.result
            )
        
        # Real-time Events Endpoint
        @self.app.websocket("/api/v1/events")
        async def websocket_events(websocket: WebSocket):
            """WebSocket endpoint for real-time events."""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive and handle incoming messages
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "subscribe":
                        # Handle event subscription
                        subscription = EventSubscription(**message.get("data", {}))
                        self.event_subscribers[str(websocket)] = subscription
                    
            except Exception as e:
                self.logger.error(f"WebSocket error: {str(e)}")
            finally:
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
                if str(websocket) in self.event_subscribers:
                    del self.event_subscribers[str(websocket)]
    
    async def _log_inspection_event(self, report: InspectionReport, user_id: str):
        """Log inspection event for audit trail."""
        event = ManufacturingEvent(
            event_type="quality_inspection",
            source_component=self.component_id,
            priority=Priority.HIGH if report.inspection_result == InspectionResult.FAIL else Priority.NORMAL,
            data={
                "part_id": report.part_id,
                "result": report.inspection_result.name,
                "score": report.overall_score,
                "defect_count": report.defect_count,
                "user_id": user_id
            }
        )
        
        # Broadcast to WebSocket subscribers
        await self._broadcast_event(event)
    
    async def _broadcast_event(self, event: ManufacturingEvent):
        """Broadcast event to WebSocket subscribers."""
        if not self.websocket_connections:
            return
        
        event_data = {
            "type": "event",
            "data": event.to_dict()
        }
        
        disconnected_connections = []
        
        for websocket in self.websocket_connections:
            try:
                # Check if this subscriber wants this event
                subscription = self.event_subscribers.get(str(websocket))
                if subscription and not self._should_send_event(event, subscription):
                    continue
                
                await websocket.send_text(json.dumps(event_data))
            except Exception as e:
                self.logger.warning(f"Failed to send event to WebSocket: {str(e)}")
                disconnected_connections.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected_connections:
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)
            if str(websocket) in self.event_subscribers:
                del self.event_subscribers[str(websocket)]
    
    def _should_send_event(self, event: ManufacturingEvent, subscription: EventSubscription) -> bool:
        """Check if event should be sent to subscriber."""
        # Filter by event type
        if subscription.event_types and event.event_type not in subscription.event_types:
            return False
        
        # Filter by priority
        if subscription.priority_filter:
            min_priority = Priority[subscription.priority_filter.upper()]
            if event.priority.value > min_priority.value:
                return False
        
        # Filter by component
        if subscription.component_filter and event.source_component != subscription.component_filter:
            return False
        
        return True
    
    def _defect_to_dict(self, defect) -> Dict[str, Any]:
        """Convert defect detection to dictionary."""
        return {
            "type": defect.defect_type.value,
            "confidence": defect.confidence,
            "severity": defect.severity,
            "bounding_box": {
                "x": defect.bounding_box.x,
                "y": defect.bounding_box.y,
                "width": defect.bounding_box.width,
                "height": defect.bounding_box.height
            },
            "description": defect.description,
            "timestamp": defect.detection_timestamp.isoformat()
        }
    
    def _measurement_to_dict(self, measurement) -> Dict[str, Any]:
        """Convert quality measurement to dictionary."""
        return {
            "type": measurement.measurement_type,
            "value": measurement.value,
            "unit": measurement.unit,
            "within_tolerance": measurement.within_tolerance,
            "tolerance_min": measurement.tolerance_min,
            "tolerance_max": measurement.tolerance_max,
            "confidence": measurement.confidence,
            "timestamp": measurement.measurement_timestamp.isoformat()
        }
    
    def _status_to_response(self, status: MachineStatus) -> MachineStatusResponse:
        """Convert machine status to response model."""
        return MachineStatusResponse(
            machine_id=status.machine_id,
            state=status.state.name,
            is_operational=status.is_operational,
            program_name=status.program_name,
            feedrate=status.feedrate,
            axis_positions={name: {"position": pos.position, "unit": pos.unit} 
                          for name, pos in status.axis_positions.items()},
            alarms=status.alarms,
            timestamp=status.timestamp
        )
    
    async def initialize(self) -> OperationResult[bool]:
        """Initialize API server."""
        try:
            # Initialize components if provided in config
            if self.config.get('quality_inspector_config'):
                self.quality_inspector = QualityInspector("api_quality_inspector", self.config['quality_inspector_config'])
                await self.quality_inspector.initialize()
            
            if self.config.get('cnc_manager_config'):
                self.cnc_manager = CNCManager("api_cnc_manager", self.config['cnc_manager_config'])
                await self.cnc_manager.initialize()
            
            self.set_state(ComponentState.READY, "API server initialized")
            return OperationResult.success_result(True)
            
        except Exception as e:
            return OperationResult.error_result(
                f"Failed to initialize API server: {str(e)}",
                error_code="INITIALIZATION_ERROR"
            )
    
    async def start_server(self) -> OperationResult[bool]:
        """Start the API server."""
        try:
            config = uvicorn.Config(
                app=self.app,
                host=self.host,
                port=self.port,
                workers=self.workers,
                log_level="info"
            )
            
            self.server = uvicorn.Server(config)
            
            # Start server in background
            await self.add_task(self.server.serve())
            
            self.set_state(ComponentState.RUNNING, "API server started")
            return OperationResult.success_result(True)
            
        except Exception as e:
            return OperationResult.error_result(
                f"Failed to start API server: {str(e)}",
                error_code="SERVER_START_ERROR"
            )
    
    async def shutdown(self) -> OperationResult[bool]:
        """Shutdown API server."""
        try:
            if self.server:
                self.server.should_exit = True
            
            # Close WebSocket connections
            for websocket in self.websocket_connections.copy():
                try:
                    await websocket.close()
                except Exception:
                    pass
            
            # Shutdown components
            if self.quality_inspector:
                await self.quality_inspector.shutdown()
            
            if self.cnc_manager:
                await self.cnc_manager.shutdown()
            
            return await super().shutdown()
            
        except Exception as e:
            return OperationResult.error_result(
                f"Error during API shutdown: {str(e)}",
                error_code="SHUTDOWN_ERROR"
            )


# Convenience function to create and run API server
async def create_api_server(config: Optional[Dict[str, Any]] = None) -> ManufacturingAPI:
    """Create and initialize API server."""
    api = ManufacturingAPI("manufacturing_api", config)
    
    init_result = await api.initialize()
    if not init_result.success:
        raise RuntimeError(f"Failed to initialize API: {init_result.error}")
    
    return api


def run_api_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: int = 1,
    config: Optional[Dict[str, Any]] = None
):
    """Run the API server directly."""
    if FastAPI is None:
        raise ImportError("FastAPI not available. Install fastapi and uvicorn packages.")
    
    # Create basic config
    server_config = {
        "host": host,
        "port": port,
        "workers": workers
    }
    
    if config:
        server_config.update(config)
    
    # Create and run server
    async def main():
        api = await create_api_server(server_config)
        await api.start_server()
        await api.wait_for_shutdown()
    
    asyncio.run(main())


# Export public interface
__all__ = [
    'APIResponse',
    'HealthCheckResponse',
    'InspectionRequest',
    'InspectionResponse',
    'MachineStatusResponse',
    'CommandRequest',
    'EventSubscription',
    'ManufacturingAPI',
    'create_api_server',
    'run_api_server'
]
