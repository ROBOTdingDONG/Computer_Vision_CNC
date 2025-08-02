"""
Core exceptions for the Computer Vision CNC Manufacturing Platform.

This module defines the base exception hierarchy and manufacturing-specific
exceptions with proper error codes and compliance tracking.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for manufacturing environments."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    SAFETY_CRITICAL = "safety_critical"


class ErrorCategory(Enum):
    """Error categories for manufacturing systems."""
    CONFIGURATION = "configuration"
    HARDWARE = "hardware"
    NETWORK = "network"
    SECURITY = "security"
    QUALITY = "quality"
    MAINTENANCE = "maintenance"
    COMPLIANCE = "compliance"
    COMPUTER_VISION = "computer_vision"
    CNC_INTEGRATION = "cnc_integration"


class CVCNCException(Exception):
    """
    Base exception for Computer Vision CNC Manufacturing Platform.
    
    All platform exceptions inherit from this base class to provide
    consistent error handling and logging for manufacturing environments.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.CONFIGURATION,
        details: Optional[Dict[str, Any]] = None,
        safety_impact: bool = False,
        compliance_impact: bool = False,
        user_action: Optional[str] = None,
        technical_action: Optional[str] = None
    ):
        super().__init__(message)
        
        self.message = message
        self.error_code = error_code or self._generate_error_code()
        self.severity = severity
        self.category = category
        self.details = details or {}
        self.safety_impact = safety_impact
        self.compliance_impact = compliance_impact
        self.user_action = user_action
        self.technical_action = technical_action
        self.timestamp = datetime.utcnow()
        
        # Log the exception based on severity
        self._log_exception()
    
    def _generate_error_code(self) -> str:
        """Generate a unique error code based on exception type and timestamp."""
        class_name = self.__class__.__name__
        timestamp_part = self.timestamp.strftime("%Y%m%d%H%M%S")
        return f"{class_name.upper()}_{timestamp_part}"
    
    def _log_exception(self) -> None:
        """Log the exception with appropriate level based on severity."""
        log_message = f"[{self.error_code}] {self.message}"
        
        if self.severity == ErrorSeverity.CRITICAL or self.safety_impact:
            logger.critical(log_message, extra=self.to_dict())
        elif self.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra=self.to_dict())
        elif self.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra=self.to_dict())
        else:
            logger.info(log_message, extra=self.to_dict())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging and serialization."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "details": self.details,
            "safety_impact": self.safety_impact,
            "compliance_impact": self.compliance_impact,
            "user_action": self.user_action,
            "technical_action": self.technical_action,
            "timestamp": self.timestamp.isoformat(),
            "exception_type": self.__class__.__name__
        }


class ConfigurationError(CVCNCException):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        kwargs.setdefault('category', ErrorCategory.CONFIGURATION)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('user_action', 'Check configuration settings and restart service')
        
        if config_key:
            kwargs.setdefault('details', {}).update({'config_key': config_key})
        
        super().__init__(message, **kwargs)


class DatabaseError(CVCNCException):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        kwargs.setdefault('category', ErrorCategory.HARDWARE)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('user_action', 'Contact system administrator')
        kwargs.setdefault('technical_action', 'Check database connectivity and logs')
        
        if query:
            kwargs.setdefault('details', {}).update({'failed_query': query})
        
        super().__init__(message, **kwargs)


class SecurityError(CVCNCException):
    """Exception raised for security-related errors."""
    
    def __init__(self, message: str, security_event: Optional[str] = None, **kwargs):
        kwargs.setdefault('category', ErrorCategory.SECURITY)
        kwargs.setdefault('severity', ErrorSeverity.CRITICAL)
        kwargs.setdefault('compliance_impact', True)
        kwargs.setdefault('user_action', 'Contact security administrator immediately')
        kwargs.setdefault('technical_action', 'Review security logs and audit access')
        
        if security_event:
            kwargs.setdefault('details', {}).update({'security_event': security_event})
        
        super().__init__(message, **kwargs)


class ManufacturingError(CVCNCException):
    """Exception raised for manufacturing process errors."""
    
    def __init__(self, message: str, machine_id: Optional[str] = None, **kwargs):
        kwargs.setdefault('category', ErrorCategory.HARDWARE)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('safety_impact', True)
        kwargs.setdefault('user_action', 'Stop production and check machine status')
        kwargs.setdefault('technical_action', 'Inspect machine and review sensor data')
        
        if machine_id:
            kwargs.setdefault('details', {}).update({'machine_id': machine_id})
        
        super().__init__(message, **kwargs)


class QualityControlError(CVCNCException):
    """Exception raised for quality control errors."""
    
    def __init__(self, message: str, part_id: Optional[str] = None, **kwargs):
        kwargs.setdefault('category', ErrorCategory.QUALITY)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('compliance_impact', True)
        kwargs.setdefault('user_action', 'Quarantine part and review quality standards')
        kwargs.setdefault('technical_action', 'Calibrate inspection equipment')
        
        if part_id:
            kwargs.setdefault('details', {}).update({'part_id': part_id})
        
        super().__init__(message, **kwargs)


class ComputerVisionError(CVCNCException):
    """Exception raised for computer vision processing errors."""
    
    def __init__(self, message: str, image_id: Optional[str] = None, **kwargs):
        kwargs.setdefault('category', ErrorCategory.COMPUTER_VISION)
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        kwargs.setdefault('user_action', 'Check camera settings and lighting conditions')
        kwargs.setdefault('technical_action', 'Review image processing logs and model performance')
        
        if image_id:
            kwargs.setdefault('details', {}).update({'image_id': image_id})
        
        super().__init__(message, **kwargs)


class CNCIntegrationError(CVCNCException):
    """Exception raised for CNC machine integration errors."""
    
    def __init__(self, message: str, cnc_machine: Optional[str] = None, **kwargs):
        kwargs.setdefault('category', ErrorCategory.CNC_INTEGRATION)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('safety_impact', True)
        kwargs.setdefault('user_action', 'Check CNC machine connectivity and status')
        kwargs.setdefault('technical_action', 'Verify network connection and protocol settings')
        
        if cnc_machine:
            kwargs.setdefault('details', {}).update({'cnc_machine': cnc_machine})
        
        super().__init__(message, **kwargs)


class NetworkError(CVCNCException):
    """Exception raised for network communication errors."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, **kwargs):
        kwargs.setdefault('category', ErrorCategory.NETWORK)
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        kwargs.setdefault('user_action', 'Check network connectivity')
        kwargs.setdefault('technical_action', 'Verify network configuration and firewall rules')
        
        if endpoint:
            kwargs.setdefault('details', {}).update({'endpoint': endpoint})
        
        super().__init__(message, **kwargs)


class ComplianceError(CVCNCException):
    """Exception raised for compliance violations."""
    
    def __init__(self, message: str, standard: Optional[str] = None, **kwargs):
        kwargs.setdefault('category', ErrorCategory.COMPLIANCE)
        kwargs.setdefault('severity', ErrorSeverity.CRITICAL)
        kwargs.setdefault('compliance_impact', True)
        kwargs.setdefault('user_action', 'Contact compliance officer immediately')
        kwargs.setdefault('technical_action', 'Review compliance documentation and audit logs')
        
        if standard:
            kwargs.setdefault('details', {}).update({'violated_standard': standard})
        
        super().__init__(message, **kwargs)


class MaintenanceError(CVCNCException):
    """Exception raised for maintenance-related errors."""
    
    def __init__(self, message: str, maintenance_task: Optional[str] = None, **kwargs):
        kwargs.setdefault('category', ErrorCategory.MAINTENANCE)
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        kwargs.setdefault('user_action', 'Schedule maintenance as soon as possible')
        kwargs.setdefault('technical_action', 'Review maintenance logs and sensor data')
        
        if maintenance_task:
            kwargs.setdefault('details', {}).update({'maintenance_task': maintenance_task})
        
        super().__init__(message, **kwargs)


class SafetyCriticalError(CVCNCException):
    """Exception raised for safety-critical situations requiring immediate attention."""
    
    def __init__(self, message: str, safety_system: Optional[str] = None, **kwargs):
        kwargs.setdefault('severity', ErrorSeverity.SAFETY_CRITICAL)
        kwargs.setdefault('safety_impact', True)
        kwargs.setdefault('user_action', 'EMERGENCY STOP - Evacuate area if necessary')
        kwargs.setdefault('technical_action', 'Activate emergency procedures and contact safety officer')
        
        if safety_system:
            kwargs.setdefault('details', {}).update({'safety_system': safety_system})
        
        super().__init__(message, **kwargs)


def handle_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    notify_operators: bool = False
) -> None:
    """
    Global exception handler for manufacturing environment.
    
    Args:
        exception: The exception to handle
        context: Additional context information
        notify_operators: Whether to send notifications to operators
    """
    # Convert to CVCNCException if needed
    if not isinstance(exception, CVCNCException):
        cv_exception = CVCNCException(
            message=str(exception),
            details=context,
            severity=ErrorSeverity.MEDIUM
        )
    else:
        cv_exception = exception
    
    # Log the exception
    logger.error(f"Exception handled: {cv_exception.to_dict()}")
    
    # Send notifications for critical errors
    if (cv_exception.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.SAFETY_CRITICAL] 
        or cv_exception.safety_impact 
        or notify_operators):
        _send_exception_notification(cv_exception)
    
    # Trigger compliance reporting if needed
    if cv_exception.compliance_impact:
        _trigger_compliance_reporting(cv_exception)


def _send_exception_notification(exception: CVCNCException) -> None:
    """Send notification to operators about critical exceptions."""
    # This would integrate with notification system
    logger.critical(f"OPERATOR NOTIFICATION: {exception.message}")


def _trigger_compliance_reporting(exception: CVCNCException) -> None:
    """Trigger compliance reporting for exceptions that impact compliance."""
    # This would integrate with compliance reporting system
    logger.warning(f"COMPLIANCE IMPACT: {exception.message}")


# Export all exception classes
__all__ = [
    'CVCNCException',
    'ConfigurationError',
    'DatabaseError', 
    'SecurityError',
    'ManufacturingError',
    'QualityControlError',
    'ComputerVisionError',
    'CNCIntegrationError',
    'NetworkError',
    'ComplianceError',
    'MaintenanceError',
    'SafetyCriticalError',
    'ErrorSeverity',
    'ErrorCategory',
    'handle_exception'
]
