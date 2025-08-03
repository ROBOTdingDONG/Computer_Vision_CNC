"""
Core module for the Computer Vision CNC Manufacturing Platform.

This module provides the foundational components, base classes, and
configuration management for the entire platform.
"""

from .base import *
from .config import *

__all__ = [
    # From base module
    "BaseManufacturingComponent",
    "BaseAsyncComponent", 
    "OperationResult",
    "ComponentState",
    "ManufacturingException",
    "SafetyException",
    "QualityException",
    "safety_context",
    
    # From config module
    "PlatformConfig",
    "ComputerVisionConfig",
    "CNCConfig",
    "APIConfig",
    "get_config",
    "default_config"
]
