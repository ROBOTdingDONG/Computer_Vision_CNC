"""
Computer Vision CNC Manufacturing Platform Test Configuration

This module provides pytest configuration and fixtures for comprehensive testing
of the manufacturing computer vision platform.
"""

import os
import sys
import pytest
import logging
import tempfile
import numpy as np
from typing import Generator, Dict, Any
from unittest.mock import Mock, MagicMock
from pathlib import Path

# Add src to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def pytest_configure(config):
    """Configure pytest with custom markers for manufacturing tests."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for system components"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and latency tests"
    )
    config.addinivalue_line(
        "markers", "security: Security and compliance tests"
    )
    config.addinivalue_line(
        "markers", "manufacturing: Manufacturing-specific functionality tests"
    )
    config.addinivalue_line(
        "markers", "cnc_integration: CNC manufacturer integration tests"
    )
    config.addinivalue_line(
        "markers", "computer_vision: Computer vision algorithm tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests (>5 seconds)"
    )
    config.addinivalue_line(
        "markers", "gpu: Tests requiring GPU hardware"
    )
    config.addinivalue_line(
        "markers", "hardware: Tests requiring specific hardware"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        
        # Add slow marker for tests taking longer than 5 seconds
        if hasattr(item, 'pytestmark'):
            for mark in item.pytestmark:
                if mark.name == 'timeout' and mark.args[0] > 5:
                    item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Provide test configuration settings."""
    return {
        "max_latency_ms": 20,
        "min_accuracy": 0.95,
        "test_image_size": (480, 640, 3),
        "test_batch_size": 8,
        "cnc_simulator_port": 8080,
        "test_data_path": Path(__file__).parent / "data",
        "manufacturing_standards": ["MTConnect", "OPC-UA", "IEC62443"],
        "supported_cnc_manufacturers": ["Mazak", "DMG_Mori", "Okuma", "Haas", "Fanuc"]
    }


@pytest.fixture(scope="session")
def temp_directory() -> Generator[Path, None, None]:
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_image() -> np.ndarray:
    """Generate a sample test image for computer vision tests."""
    # Create a synthetic test image with known patterns
    image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Add some geometric patterns for detection testing
    cv2 = pytest.importorskip("cv2")
    cv2.rectangle(image, (100, 100), (200, 200), (255, 0, 0), -1)
    cv2.circle(image, (400, 300), 50, (0, 255, 0), -1)
    
    return image


@pytest.fixture
def defective_image() -> np.ndarray:
    """Generate a sample image with simulated defects."""
    cv2 = pytest.importorskip("cv2")
    
    # Create base image
    image = np.ones((480, 640, 3), dtype=np.uint8) * 128
    
    # Add simulated defects
    # Scratch defect
    cv2.line(image, (50, 50), (150, 150), (0, 0, 0), 2)
    
    # Dent defect (darker circular area)
    cv2.circle(image, (300, 200), 20, (80, 80, 80), -1)
    
    # Contamination (irregular bright spot)
    cv2.ellipse(image, (500, 350), (15, 25), 45, 0, 360, (200, 200, 200), -1)
    
    return image


@pytest.fixture
def mock_cnc_machine() -> Mock:
    """Provide a mock CNC machine for integration tests."""
    cnc = Mock()
    cnc.connect.return_value = True
    cnc.disconnect.return_value = True
    cnc.is_connected.return_value = True
    cnc.get_status.return_value = {
        "machine_id": "TEST_CNC_001",
        "status": "ACTIVE",
        "mode": "AUTOMATIC",
        "program": "O1234",
        "line_number": 125,
        "spindle_speed": 1500,
        "feed_rate": 150,
        "tool_number": 5,
        "position": {"x": 100.5, "y": 50.2, "z": 25.0},
        "alarms": [],
        "timestamp": "2025-01-01T12:00:00Z"
    }
    cnc.execute_command.return_value = {"success": True, "message": "Command executed"}
    
    return cnc


@pytest.fixture
def mock_camera() -> Mock:
    """Provide a mock industrial camera for vision tests."""
    camera = Mock()
    camera.connect.return_value = True
    camera.disconnect.return_value = True
    camera.is_connected.return_value = True
    camera.capture_image.return_value = np.random.randint(
        0, 255, (480, 640, 3), dtype=np.uint8
    )
    camera.get_settings.return_value = {
        "exposure": 10000,
        "gain": 1.0,
        "resolution": (640, 480),
        "frame_rate": 30,
        "trigger_mode": "software"
    }
    camera.set_settings.return_value = True
    
    return camera


@pytest.fixture
def mock_ml_model() -> Mock:
    """Provide a mock machine learning model for testing."""
    model = Mock()
    model.predict.return_value = [
        {
            "confidence": 0.95,
            "class_name": "surface_defect",
            "bounding_box": (100, 100, 50, 50),
            "timestamp": "2025-01-01T12:00:00Z"
        }
    ]
    model.is_loaded.return_value = True
    model.load.return_value = True
    model.get_accuracy.return_value = 0.98
    
    return model


@pytest.fixture
def manufacturing_test_data() -> Dict[str, Any]:
    """Provide manufacturing-specific test data."""
    return {
        "oee_data": {
            "availability": 0.95,
            "performance": 0.85,
            "quality": 0.98,
            "expected_oee": 0.7913
        },
        "tool_wear_data": {
            "cutting_time": 120.5,
            "feed_rate": 150,
            "spindle_speed": 1500,
            "material": "aluminum",
            "tool_type": "carbide_end_mill"
        },
        "quality_metrics": {
            "parts_produced": 1000,
            "parts_rejected": 15,
            "rework_count": 8,
            "scrap_count": 7,
            "first_pass_yield": 0.985
        }
    }


@pytest.fixture
def security_test_config() -> Dict[str, Any]:
    """Provide security testing configuration."""
    return {
        "test_users": {
            "operator": {"role": "operator", "permissions": ["view", "operate"]},
            "supervisor": {"role": "supervisor", "permissions": ["view", "operate", "configure"]},
            "admin": {"role": "admin", "permissions": ["view", "operate", "configure", "manage"]}
        },
        "encryption_keys": {
            "test_key": "test_encryption_key_for_testing_only"
        },
        "compliance_standards": {
            "IEC62443": {"level": 2, "requirements": ["authentication", "authorization", "encryption"]},
            "ISO27001": {"controls": ["access_control", "cryptography", "incident_management"]}
        }
    }


@pytest.fixture
def performance_benchmarks() -> Dict[str, float]:
    """Provide performance benchmark targets."""
    return {
        "max_latency_ms": 20.0,
        "min_throughput_fps": 30.0,
        "max_memory_mb": 512.0,
        "max_cpu_percent": 80.0,
        "min_accuracy": 0.95,
        "max_false_positive_rate": 0.05,
        "max_false_negative_rate": 0.03
    }


@pytest.fixture(scope="session")
def cnc_simulator():
    """Start a CNC machine simulator for integration tests."""
    # This would start an actual CNC simulator
    # For now, return a mock configuration
    return {
        "host": "localhost",
        "port": 8080,
        "protocol": "MTConnect",
        "device_id": "TEST_CNC_SIMULATOR"
    }


@pytest.fixture
def test_database(temp_directory):
    """Provide a test database for integration tests."""
    db_path = temp_directory / "test_manufacturing.db"
    
    # Initialize test database with sample data
    # This would use the actual database setup code
    return {
        "connection_string": f"sqlite:///{db_path}",
        "tables": ["machines", "inspections", "quality_data", "tool_life"]
    }


# Custom assertion helpers
def assert_latency_requirement(execution_time_ms: float, max_latency_ms: float = 20.0):
    """Assert that execution time meets manufacturing latency requirements."""
    assert execution_time_ms <= max_latency_ms, (
        f"Execution time {execution_time_ms:.2f}ms exceeds "
        f"manufacturing requirement of {max_latency_ms}ms"
    )


def assert_accuracy_requirement(accuracy: float, min_accuracy: float = 0.95):
    """Assert that accuracy meets manufacturing quality requirements."""
    assert accuracy >= min_accuracy, (
        f"Accuracy {accuracy:.3f} below manufacturing requirement of {min_accuracy:.3f}"
    )


def assert_manufacturing_compliance(component: str, standards: list):
    """Assert that component meets manufacturing compliance standards."""
    required_standards = ["MTConnect", "OPC-UA", "IEC62443"]
    missing_standards = set(required_standards) - set(standards)
    
    assert not missing_standards, (
        f"Component {component} missing compliance with standards: {missing_standards}"
    )


# Performance measurement utilities
@pytest.fixture
def performance_monitor():
    """Provide performance monitoring utilities."""
    import time
    import psutil
    import threading
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.peak_memory = 0
            self.peak_cpu = 0
            self._monitoring = False
            self._monitor_thread = None
        
        def start(self):
            self.start_time = time.perf_counter()
            self.peak_memory = 0
            self.peak_cpu = 0
            self._monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitor_resources)
            self._monitor_thread.start()
        
        def stop(self):
            self.end_time = time.perf_counter()
            self._monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join()
        
        def _monitor_resources(self):
            process = psutil.Process()
            while self._monitoring:
                self.peak_memory = max(self.peak_memory, process.memory_info().rss / 1024 / 1024)
                self.peak_cpu = max(self.peak_cpu, process.cpu_percent())
                time.sleep(0.1)
        
        @property
        def execution_time_ms(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return 0
        
        def assert_performance_requirements(self, benchmarks: Dict[str, float]):
            assert_latency_requirement(self.execution_time_ms, benchmarks["max_latency_ms"])
            assert self.peak_memory <= benchmarks["max_memory_mb"], (
                f"Peak memory {self.peak_memory:.1f}MB exceeds limit {benchmarks['max_memory_mb']}MB"
            )
            assert self.peak_cpu <= benchmarks["max_cpu_percent"], (
                f"Peak CPU {self.peak_cpu:.1f}% exceeds limit {benchmarks['max_cpu_percent']}%"
            )
    
    return PerformanceMonitor()


# Error injection utilities for robustness testing
@pytest.fixture
def error_injector():
    """Provide error injection utilities for robustness testing."""
    
    class ErrorInjector:
        @staticmethod
        def inject_network_error():
            """Simulate network connectivity issues."""
            from unittest.mock import patch
            return patch('socket.socket.connect', side_effect=ConnectionError("Network error"))
        
        @staticmethod
        def inject_memory_error():
            """Simulate memory allocation failures."""
            from unittest.mock import patch
            return patch('numpy.zeros', side_effect=MemoryError("Out of memory"))
        
        @staticmethod
        def inject_device_error():
            """Simulate device communication failures."""
            from unittest.mock import patch
            return patch('serial.Serial.read', side_effect=IOError("Device not responding"))
        
        @staticmethod
        def inject_data_corruption():
            """Simulate data corruption scenarios."""
            def corrupt_data(data):
                if isinstance(data, np.ndarray):
                    corrupted = data.copy()
                    # Randomly corrupt 1% of pixels
                    corruption_mask = np.random.random(data.shape) < 0.01
                    corrupted[corruption_mask] = 255
                    return corrupted
                return data
            
            return corrupt_data
    
    return ErrorInjector()


# Manufacturing scenario generators
@pytest.fixture
def manufacturing_scenarios():
    """Provide various manufacturing test scenarios."""
    
    return {
        "high_speed_machining": {
            "spindle_speed": 15000,
            "feed_rate": 2000,
            "expected_cycle_time": 45,
            "quality_tolerance": 0.001
        },
        "precision_machining": {
            "spindle_speed": 3000,
            "feed_rate": 100,
            "expected_cycle_time": 180,
            "quality_tolerance": 0.0001
        },
        "production_run": {
            "part_count": 1000,
            "batch_size": 50,
            "quality_target": 0.99,
            "downtime_allowance": 0.05
        },
        "tool_change_cycle": {
            "tools_in_magazine": 20,
            "change_time_seconds": 5,
            "wear_monitoring": True,
            "life_tracking": True
        }
    }
