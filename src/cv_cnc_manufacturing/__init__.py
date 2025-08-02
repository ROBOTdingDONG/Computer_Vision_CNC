"""
Computer Vision CNC Manufacturing Platform

Enterprise-grade computer vision platform for CNC manufacturing optimization.
Implements Industry 4.0 technologies with IEC 62443 security compliance.

Version: 1.0.0
License: MIT with Manufacturing Disclaimers
Author: Computer Vision CNC Platform Team
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Version information
__version__ = "1.0.0"
__version_info__ = (1, 0, 0)
__author__ = "Computer Vision CNC Platform Team"
__email__ = "team@cv-cnc-platform.com"
__license__ = "MIT"
__copyright__ = "Copyright 2025 Computer Vision CNC Platform Team"

# Platform information
__platform_name__ = "Computer Vision CNC Manufacturing Platform"
__platform_description__ = "Enterprise Computer Vision CNC Manufacturing Optimization Platform"
__platform_url__ = "https://github.com/ROBOTdingDONG/Computer_Vision_CNC"

# Manufacturing compliance information
__compliance_standards__ = [
    "ISO 9001:2015",
    "IATF 16949:2016", 
    "IEC 62443",
    "NIST Cybersecurity Framework"
]

__export_control__ = "EAR99"
__safety_rating__ = "Category 3 (EN ISO 13849-1)"

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('cv_cnc_manufacturing.log')
    ]
)

# Package logger
logger = logging.getLogger(__name__)

# Platform directories
PACKAGE_ROOT = Path(__file__).parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
CONFIG_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
CERTS_DIR = PROJECT_ROOT / "certs"

# Ensure required directories exist
for directory in [DATA_DIR, LOGS_DIR, CERTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Manufacturing safety notice
SAFETY_NOTICE = """
⚠️  MANUFACTURING SAFETY NOTICE ⚠️

This software is designed for industrial manufacturing environments.
Please observe the following safety requirements:

1. EMERGENCY STOP: Always maintain access to emergency stop controls
2. SAFETY SYSTEMS: Do not bypass or disable safety interlocks
3. QUALIFIED PERSONNEL: Only trained personnel should operate this system
4. COMPLIANCE: Ensure compliance with local safety regulations
5. MAINTENANCE: Follow scheduled maintenance procedures
6. DOCUMENTATION: Maintain complete operational documentation

For emergency support: emergency@cv-cnc-platform.com
"""

# Export control notice
EXPORT_CONTROL_NOTICE = """
🌍 EXPORT CONTROL NOTICE 🌍

This software may be subject to export control regulations.
Users are responsible for compliance with applicable laws.

- Classification: EAR99
- Review export regulations before international use
- Restricted countries may require special licenses
- Contact legal@cv-cnc-platform.com for guidance
"""

def get_version() -> str:
    """Get the current version string."""
    return __version__

def get_version_info() -> tuple:
    """Get version information as tuple."""
    return __version_info__

def get_platform_info() -> dict:
    """Get comprehensive platform information."""
    return {
        "name": __platform_name__,
        "version": __version__,
        "description": __platform_description__,
        "author": __author__,
        "license": __license__,
        "compliance_standards": __compliance_standards__,
        "export_control": __export_control__,
        "safety_rating": __safety_rating__,
        "url": __platform_url__
    }

def print_safety_notice() -> None:
    """Print manufacturing safety notice."""
    print(SAFETY_NOTICE)

def print_export_control_notice() -> None:
    """Print export control notice."""
    print(EXPORT_CONTROL_NOTICE)

def initialize_platform(
    config_path: Optional[Path] = None,
    log_level: str = "INFO",
    show_notices: bool = True
) -> None:
    """
    Initialize the Computer Vision CNC Manufacturing Platform.
    
    Args:
        config_path: Path to configuration file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        show_notices: Whether to display safety and compliance notices
    """
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    logger.info(f"Initializing {__platform_name__} v{__version__}")
    
    # Display notices for manufacturing safety
    if show_notices:
        print_safety_notice()
        print_export_control_notice()
    
    # Log platform information
    logger.info(f"Platform: {__platform_name__}")
    logger.info(f"Version: {__version__}")
    logger.info(f"Compliance: {', '.join(__compliance_standards__)}")
    logger.info(f"Export Control: {__export_control__}")
    logger.info(f"Safety Rating: {__safety_rating__}")
    
    # Validate environment
    _validate_environment()
    
    logger.info("Platform initialization completed successfully")

def _validate_environment() -> None:
    """Validate the runtime environment for manufacturing requirements."""
    import platform as py_platform
    
    # Check Python version
    if sys.version_info < (3, 8):
        raise RuntimeError(
            f"Python 3.8+ required for manufacturing compliance. "
            f"Current version: {sys.version}"
        )
    
    # Log system information
    logger.info(f"Python: {sys.version}")
    logger.info(f"Platform: {py_platform.system()} {py_platform.release()}")
    logger.info(f"Architecture: {py_platform.machine()}")
    
    # Check required directories
    for directory in [CONFIG_DIR, DATA_DIR, LOGS_DIR, CERTS_DIR]:
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
        else:
            logger.debug(f"Directory validated: {directory}")

# Module imports for easy access
try:
    from .core import *
    from .computer_vision import *
    from .cnc_integration import *
    from .quality_control import *
    from .predictive_maintenance import *
    from .api import *
    from .security import *
    from .compliance import *
    from .utils import *
    
    logger.debug("All platform modules imported successfully")
    
except ImportError as e:
    logger.warning(f"Some platform modules could not be imported: {e}")
    logger.info("This is normal during initial setup or testing")

# Platform metadata for setuptools
__all__ = [
    # Version information
    "__version__",
    "__version_info__", 
    "__author__",
    "__email__",
    "__license__",
    "__copyright__",
    
    # Platform information
    "__platform_name__",
    "__platform_description__",
    "__platform_url__",
    "__compliance_standards__",
    "__export_control__",
    "__safety_rating__",
    
    # Functions
    "get_version",
    "get_version_info", 
    "get_platform_info",
    "print_safety_notice",
    "print_export_control_notice",
    "initialize_platform",
    
    # Constants
    "PACKAGE_ROOT",
    "PROJECT_ROOT", 
    "CONFIG_DIR",
    "DATA_DIR",
    "LOGS_DIR",
    "CERTS_DIR",
    "SAFETY_NOTICE",
    "EXPORT_CONTROL_NOTICE",
    
    # Logger
    "logger"
]
