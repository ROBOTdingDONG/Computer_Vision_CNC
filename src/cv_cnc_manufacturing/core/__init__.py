"""
Core module for Computer Vision CNC Manufacturing Platform.

This module provides the foundational components and base classes
for the entire manufacturing optimization platform.
"""

from .base import *
from .config import *
from .database import *
from .events import *
from .exceptions import *
from .logging import *
from .metrics import *
from .models import *
from .services import *

__all__ = [
    # Base classes and interfaces
    "BaseService",
    "BaseModel", 
    "BaseController",
    "BaseRepository",
    
    # Configuration
    "Config",
    "DatabaseConfig",
    "SecurityConfig",
    "ManufacturingConfig",
    
    # Database
    "DatabaseManager",
    "Session",
    "Base",
    
    # Events
    "EventBus",
    "Event",
    "EventHandler",
    
    # Exceptions
    "CVCNCException",
    "ConfigurationError",
    "DatabaseError",
    "SecurityError",
    "ManufacturingError",
    
    # Logging
    "get_logger",
    "setup_logging",
    "AuditLogger",
    
    # Metrics
    "MetricsCollector",
    "PerformanceMonitor",
    
    # Models
    "User",
    "Machine", 
    "QualityRecord",
    "MaintenanceRecord",
    
    # Services
    "ServiceRegistry",
    "ServiceManager",
]
