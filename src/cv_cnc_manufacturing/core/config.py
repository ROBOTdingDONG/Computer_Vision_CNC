"""
Configuration management for the Computer Vision CNC Manufacturing Platform.

This module provides configuration classes and utilities for managing
platform settings across all components.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class PlatformConfig:
    """Base configuration for the manufacturing platform."""
    
    # Environment settings
    environment: str = field(default_factory=lambda: os.getenv("CV_CNC_ENV", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("CV_CNC_DEBUG", "false").lower() == "true")
    
    # Safety settings
    safety_mode: bool = field(default_factory=lambda: os.getenv("CV_CNC_SAFETY", "true").lower() == "true")
    emergency_stop_enabled: bool = True
    
    # Logging settings
    log_level: str = field(default_factory=lambda: os.getenv("CV_CNC_LOG_LEVEL", "INFO"))
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Directory settings
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("CV_CNC_DATA_DIR", "./data")))
    config_dir: Path = field(default_factory=lambda: Path(os.getenv("CV_CNC_CONFIG_DIR", "./configs")))
    logs_dir: Path = field(default_factory=lambda: Path(os.getenv("CV_CNC_LOGS_DIR", "./logs")))
    
    def __post_init__(self):
        """Ensure directories exist after initialization."""
        for directory in [self.data_dir, self.config_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)


@dataclass
class ComputerVisionConfig:
    """Configuration for computer vision components."""
    
    # Image processing settings
    max_image_size: tuple = (2048, 2048)
    supported_formats: list = field(default_factory=lambda: ["jpg", "jpeg", "png", "bmp", "tiff"])
    
    # Quality inspection settings
    defect_threshold: float = 0.8
    quality_threshold: float = 0.95
    
    # Performance settings
    batch_size: int = 1
    use_gpu: bool = field(default_factory=lambda: os.getenv("CV_CNC_USE_GPU", "false").lower() == "true")


@dataclass
class CNCConfig:
    """Configuration for CNC integration."""
    
    # Connection settings
    connection_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # MTConnect settings
    mtconnect_host: str = field(default_factory=lambda: os.getenv("CV_CNC_MTCONNECT_HOST", "localhost"))
    mtconnect_port: int = field(default_factory=lambda: int(os.getenv("CV_CNC_MTCONNECT_PORT", "5000")))
    
    # OPC-UA settings
    opcua_endpoint: str = field(default_factory=lambda: os.getenv("CV_CNC_OPCUA_ENDPOINT", "opc.tcp://localhost:4840"))
    
    # Safety settings
    emergency_stop_enabled: bool = True
    safety_zone_enabled: bool = True


@dataclass
class APIConfig:
    """Configuration for the REST API server."""
    
    # Server settings
    host: str = field(default_factory=lambda: os.getenv("CV_CNC_API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("CV_CNC_API_PORT", "8000")))
    workers: int = field(default_factory=lambda: int(os.getenv("CV_CNC_API_WORKERS", "1")))
    
    # Security settings
    secret_key: str = field(default_factory=lambda: os.getenv("CV_CNC_SECRET_KEY", "dev-secret-key-change-in-production"))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API settings
    title: str = "Computer Vision CNC Manufacturing API"
    description: str = "Enterprise Computer Vision CNC Manufacturing Platform API"
    version: str = "1.0.0"
    
    # CORS settings
    allow_origins: list = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"])
    allow_credentials: bool = True
    allow_methods: list = field(default_factory=lambda: ["*"])
    allow_headers: list = field(default_factory=lambda: ["*"])


def get_config() -> Dict[str, Any]:
    """Get the complete platform configuration."""
    return {
        "platform": PlatformConfig(),
        "computer_vision": ComputerVisionConfig(),
        "cnc": CNCConfig(),
        "api": APIConfig()
    }


def load_config_from_file(config_path: Path) -> Dict[str, Any]:
    """Load configuration from a file (placeholder implementation)."""
    # This would typically load from YAML, JSON, or TOML
    # For now, return default configuration
    return get_config()


# Default configuration instance
default_config = get_config()
