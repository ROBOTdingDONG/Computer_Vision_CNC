"""
Core base classes and interfaces for the Computer Vision CNC Manufacturing Platform.

This module provides the foundational abstractions and base classes that all
components in the manufacturing system inherit from or implement.

Safety Notice: This software is intended for industrial automation. Ensure all
safety protocols are followed and proper validation is performed before
deployment in manufacturing environments.
"""

import abc
import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Protocol, Union, Generic, TypeVar
from uuid import UUID, uuid4

# Optional imports with graceful degradation
try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    import logging as structlog
    HAS_STRUCTLOG = False

try:
    from pydantic import BaseModel, Field, validator
    HAS_PYDANTIC = True
except ImportError:
    # Create minimal replacements for Pydantic functionality
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def Field(default=None, **kwargs):
        return default
    
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    HAS_PYDANTIC = False


# Configure structured logging
if HAS_STRUCTLOG:
    logger = structlog.get_logger(__name__)
else:
    logger = structlog.getLogger(__name__)  # Use logging.getLogger when structlog not available

T = TypeVar('T')
ResultType = TypeVar('ResultType')


class ComponentState(Enum):
    """Enumeration of possible component states in the manufacturing system."""
    UNINITIALIZED = auto()
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    ERROR = auto()
    EMERGENCY_STOP = auto()
    MAINTENANCE = auto()
    SHUTDOWN = auto()


class Priority(Enum):
    """Task and event priority levels for manufacturing operations."""
    EMERGENCY = 0
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class ManufacturingException(Exception):
    """Base exception for all manufacturing-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        component: Optional[str] = None,
        severity: str = "ERROR",
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.component = component
        self.severity = severity
        self.recovery_suggestions = recovery_suggestions or []
        self.timestamp = datetime.now(timezone.utc)


class SafetyException(ManufacturingException):
    """Exception raised for safety-related issues that require immediate attention."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, severity="CRITICAL", **kwargs)


class QualityException(ManufacturingException):
    """Exception raised when quality standards are not met."""
    pass


class CommunicationException(ManufacturingException):
    """Exception raised for communication-related issues."""
    pass


@dataclass
class ComponentInfo:
    """Information about a manufacturing system component."""
    component_id: str
    component_type: str
    version: str
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    location: Optional[str] = None
    specifications: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationResult(Generic[ResultType]):
    """Standard result container for manufacturing operations."""
    success: bool
    result: Optional[ResultType] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def success_result(
        cls,
        result: ResultType,
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'OperationResult[ResultType]':
        """Create a successful operation result."""
        return cls(
            success=True,
            result=result,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
    
    @classmethod
    def error_result(
        cls,
        error: str,
        error_code: Optional[str] = None,
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'OperationResult[ResultType]':
        """Create an error operation result."""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )


class BaseManufacturingComponent(ABC):
    """
    Abstract base class for all manufacturing system components.
    
    Provides common functionality including state management, logging,
    health monitoring, and lifecycle management.
    """
    
    def __init__(
        self,
        component_id: str,
        component_type: str,
        config: Optional[Dict[str, Any]] = None
    ):
        self.component_id = component_id
        self.component_type = component_type
        self.config = config or {}
        self.state = ComponentState.UNINITIALIZED
        
        # Initialize logger with proper fallback
        if HAS_STRUCTLOG:
            self.logger = structlog.get_logger(self.__class__.__name__).bind(
                component_id=component_id,
                component_type=component_type
            )
        else:
            self.logger = structlog.getLogger(self.__class__.__name__)
        
        self._state_lock = threading.RLock()
        self._health_data: Dict[str, Any] = {}
        self._last_heartbeat = time.time()
        self._initialization_time: Optional[datetime] = None
        
        # Register for cleanup on shutdown
        import atexit
        atexit.register(self._cleanup)
    
    @property
    def is_healthy(self) -> bool:
        """Check if component is in a healthy state."""
        return self.state in {ComponentState.READY, ComponentState.RUNNING}
    
    @property
    def uptime_seconds(self) -> float:
        """Get component uptime in seconds."""
        if self._initialization_time:
            return (datetime.now(timezone.utc) - self._initialization_time).total_seconds()
        return 0.0
    
    def set_state(self, new_state: ComponentState, reason: Optional[str] = None) -> None:
        """Thread-safe state transition."""
        with self._state_lock:
            old_state = self.state
            self.state = new_state
            self.logger.info(
                "State transition",
                old_state=old_state.name,
                new_state=new_state.name,
                reason=reason
            )
            
            if new_state == ComponentState.READY and old_state == ComponentState.INITIALIZING:
                self._initialization_time = datetime.now(timezone.utc)
    
    def update_health_data(self, health_data: Dict[str, Any]) -> None:
        """Update component health monitoring data."""
        self._health_data.update(health_data)
        self._last_heartbeat = time.time()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        return {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "state": self.state.name,
            "is_healthy": self.is_healthy,
            "uptime_seconds": self.uptime_seconds,
            "last_heartbeat": self._last_heartbeat,
            "health_data": self._health_data.copy()
        }
    
    @abstractmethod
    async def initialize(self) -> OperationResult[bool]:
        """Initialize the component. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> OperationResult[bool]:
        """Shutdown the component gracefully. Must be implemented by subclasses."""
        pass
    
    async def start(self) -> OperationResult[bool]:
        """Start the component operation."""
        if self.state != ComponentState.READY:
            return OperationResult.error_result(
                f"Cannot start component in state {self.state.name}",
                error_code="INVALID_STATE"
            )
        
        self.set_state(ComponentState.RUNNING, "Component started")
        return OperationResult.success_result(True)
    
    async def stop(self) -> OperationResult[bool]:
        """Stop the component operation."""
        if self.state == ComponentState.RUNNING:
            self.set_state(ComponentState.READY, "Component stopped")
        return OperationResult.success_result(True)
    
    async def pause(self) -> OperationResult[bool]:
        """Pause the component operation."""
        if self.state == ComponentState.RUNNING:
            self.set_state(ComponentState.PAUSED, "Component paused")
            return OperationResult.success_result(True)
        return OperationResult.error_result(
            f"Cannot pause component in state {self.state.name}",
            error_code="INVALID_STATE"
        )
    
    async def resume(self) -> OperationResult[bool]:
        """Resume the component operation."""
        if self.state == ComponentState.PAUSED:
            self.set_state(ComponentState.RUNNING, "Component resumed")
            return OperationResult.success_result(True)
        return OperationResult.error_result(
            f"Cannot resume component in state {self.state.name}",
            error_code="INVALID_STATE"
        )
    
    async def emergency_stop(self) -> OperationResult[bool]:
        """Emergency stop - should be implemented by safety-critical components."""
        self.set_state(ComponentState.EMERGENCY_STOP, "Emergency stop activated")
        self.logger.critical("Emergency stop activated", component_id=self.component_id)
        return OperationResult.success_result(True)
    
    def _cleanup(self) -> None:
        """Internal cleanup method called on shutdown."""
        try:
            if hasattr(self, 'logger'):
                self.logger.info("Component cleanup initiated", component_id=self.component_id)
        except Exception:
            # Ignore cleanup errors during shutdown
            pass


class ManufacturingEventProtocol(Protocol):
    """Protocol for manufacturing events."""
    event_id: UUID
    event_type: str
    timestamp: datetime
    source_component: str
    priority: Priority
    data: Dict[str, Any]


@dataclass
class ManufacturingEvent:
    """Standard event structure for the manufacturing system."""
    event_id: UUID = field(default_factory=uuid4)
    event_type: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_component: str = ""
    priority: Priority = Priority.NORMAL
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "source_component": self.source_component,
            "priority": self.priority.name,
            "data": self.data
        }


class EventHandlerProtocol(Protocol):
    """Protocol for event handlers."""
    
    async def handle_event(self, event: ManufacturingEvent) -> OperationResult[bool]:
        """Handle a manufacturing event."""
        ...


class DataProcessorProtocol(Protocol[T]):
    """Protocol for data processors."""
    
    async def process(self, data: T) -> OperationResult[T]:
        """Process input data and return result."""
        ...


class QualityInspectorProtocol(Protocol):
    """Protocol for quality inspection components."""
    
    async def inspect(self, item: Any) -> OperationResult[Dict[str, Any]]:
        """Perform quality inspection on an item."""
        ...


class CNCControllerProtocol(Protocol):
    """Protocol for CNC machine controllers."""
    
    async def connect(self) -> OperationResult[bool]:
        """Connect to CNC machine."""
        ...
    
    async def get_status(self) -> OperationResult[Dict[str, Any]]:
        """Get current machine status."""
        ...
    
    async def send_program(self, program: str) -> OperationResult[bool]:
        """Send G-code program to machine."""
        ...


class ComputerVisionProcessorProtocol(Protocol):
    """Protocol for computer vision processors."""
    
    async def process_image(self, image: Any) -> OperationResult[Dict[str, Any]]:
        """Process an image and return analysis results."""
        ...
    
    async def detect_defects(self, image: Any) -> OperationResult[List[Dict[str, Any]]]:
        """Detect defects in an image."""
        ...


class ManufacturingConfig(BaseModel):
    """Base configuration model for manufacturing components."""
    
    component_id: str = Field(..., description="Unique component identifier")
    component_type: str = Field(..., description="Type of component")
    enabled: bool = Field(default=True, description="Whether component is enabled")
    log_level: str = Field(default="INFO", description="Logging level")
    health_check_interval: float = Field(default=30.0, description="Health check interval in seconds")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()
    
    class Config:
        """Pydantic configuration."""
        extra = "allow"  # Allow additional fields for component-specific config


class BaseAsyncComponent(BaseManufacturingComponent):
    """
    Base class for asynchronous manufacturing components.
    
    Provides async/await patterns and task management for components
    that need to run continuous operations.
    """
    
    def __init__(
        self,
        component_id: str,
        component_type: str,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(component_id, component_type, config)
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
    
    async def add_task(self, coro) -> asyncio.Task:
        """Add a managed task that will be cancelled on shutdown."""
        task = asyncio.create_task(coro)
        self._tasks.append(task)
        return task
    
    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self._shutdown_event.wait()
    
    async def shutdown(self) -> OperationResult[bool]:
        """Shutdown component and cancel all tasks."""
        self.set_state(ComponentState.SHUTDOWN, "Shutdown initiated")
        self._shutdown_event.set()
        
        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        return OperationResult.success_result(True)
    
    @asynccontextmanager
    async def operation_context(self, operation_name: str):
        """Context manager for tracking operations."""
        start_time = time.time()
        self.logger.info(f"Starting operation: {operation_name}")
        
        try:
            yield
            duration = (time.time() - start_time) * 1000
            self.logger.info(f"Completed operation: {operation_name}", duration_ms=duration)
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(
                f"Failed operation: {operation_name}",
                duration_ms=duration,
                error=str(e)
            )
            raise


# Utility functions for common operations
def create_operation_timer():
    """Create a timer for measuring operation duration."""
    start_time = time.time()
    
    def get_duration_ms() -> float:
        return (time.time() - start_time) * 1000
    
    return get_duration_ms


@contextmanager
def safety_context(component: BaseManufacturingComponent, operation: str):
    """Context manager for safety-critical operations."""
    try:
        component.logger.info(f"Starting safety operation: {operation}")
        yield
        component.logger.info(f"Completed safety operation: {operation}")
    except Exception as e:
        component.logger.critical(
            f"Safety operation failed: {operation}",
            error=str(e),
            component_id=component.component_id
        )
        # Trigger emergency stop for safety-critical failures
        asyncio.create_task(component.emergency_stop())
        raise SafetyException(f"Safety operation failed: {operation}") from e


def validate_manufacturing_compliance(component: BaseManufacturingComponent) -> bool:
    """Validate that component meets manufacturing compliance requirements."""
    # This would implement actual compliance checks
    # For now, basic validation
    required_attrs = ['component_id', 'component_type', 'state']
    return all(hasattr(component, attr) for attr in required_attrs)


# Export public interface
__all__ = [
    'ComponentState',
    'Priority',
    'ManufacturingException',
    'SafetyException',
    'QualityException',
    'CommunicationException',
    'ComponentInfo',
    'OperationResult',
    'BaseManufacturingComponent',
    'BaseAsyncComponent',
    'ManufacturingEvent',
    'ManufacturingConfig',
    'EventHandlerProtocol',
    'DataProcessorProtocol',
    'QualityInspectorProtocol',
    'CNCControllerProtocol',
    'ComputerVisionProcessorProtocol',
    'create_operation_timer',
    'safety_context',
    'validate_manufacturing_compliance'
]
