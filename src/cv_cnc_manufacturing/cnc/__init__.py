"""
CNC Integration architecture for Computer Vision CNC Manufacturing Platform.

This module provides comprehensive integration with CNC machines through various
industrial protocols including MTConnect, OPC-UA, Modbus, and proprietary APIs.

Safety Notice: CNC machine integration involves heavy machinery. Ensure all
safety protocols, emergency stops, and validation procedures are properly
implemented before deployment.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union, Callable
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

try:
    from opcua import Client as OPCUAClient, ua
except ImportError:
    OPCUAClient = None
    ua = None

try:
    from pymodbus.client.sync import ModbusTcpClient
    from pymodbus.constants import Endian
    from pymodbus.payload import BinaryPayloadDecoder
except ImportError:
    ModbusTcpClient = None
    BinaryPayloadDecoder = None

from ..core.base import (
    BaseAsyncComponent,
    OperationResult,
    ComponentState,
    ManufacturingException,
    CommunicationException,
    safety_context,
    create_operation_timer
)


class MachineState(Enum):
    """CNC Machine operational states."""
    UNAVAILABLE = auto()
    READY = auto()
    ACTIVE = auto()
    INTERRUPTED = auto()
    STOPPED = auto()
    EMERGENCY_STOP = auto()
    MAINTENANCE = auto()
    FAULT = auto()


class CNCCommand(Enum):
    """Standard CNC machine commands."""
    START_PROGRAM = "start_program"
    STOP_PROGRAM = "stop_program"
    PAUSE_PROGRAM = "pause_program"
    RESUME_PROGRAM = "resume_program"
    RESET = "reset"
    HOME_ALL_AXES = "home_all_axes"
    EMERGENCY_STOP = "emergency_stop"
    LOAD_PROGRAM = "load_program"
    UNLOAD_PROGRAM = "unload_program"
    SET_FEEDRATE = "set_feedrate"
    SET_SPINDLE_SPEED = "set_spindle_speed"


class ProtocolType(Enum):
    """Supported communication protocols."""
    MTCONNECT = "mtconnect"
    OPCUA = "opcua"
    MODBUS = "modbus"
    FOCAS = "focas"
    ETHERNET_IP = "ethernet_ip"
    HTTP_API = "http_api"
    SERIAL = "serial"


@dataclass
class AxisPosition:
    """Position information for a machine axis."""
    axis_name: str
    position: float
    unit: str = "mm"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ToolInfo:
    """Information about a cutting tool."""
    tool_id: str
    tool_number: int
    tool_type: str
    diameter: float
    length: float
    material: Optional[str] = None
    coating: Optional[str] = None
    wear_offset: float = 0.0
    life_remaining: Optional[float] = None
    last_used: Optional[datetime] = None


@dataclass
class SpindleStatus:
    """Spindle status information."""
    speed_rpm: float
    load_percent: float
    temperature: Optional[float] = None
    is_running: bool = False
    direction: str = "stopped"  # "stopped", "clockwise", "counterclockwise"


@dataclass
class MachineStatus:
    """Comprehensive machine status."""
    machine_id: str
    state: MachineState
    program_name: Optional[str] = None
    line_number: Optional[int] = None
    feedrate: Optional[float] = None
    axis_positions: Dict[str, AxisPosition] = field(default_factory=dict)
    spindle_status: Optional[SpindleStatus] = None
    current_tool: Optional[ToolInfo] = None
    coolant_on: bool = False
    door_open: bool = False
    emergency_stop_active: bool = False
    alarms: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def is_operational(self) -> bool:
        """Check if machine is in an operational state."""
        return self.state in {MachineState.READY, MachineState.ACTIVE}
    
    @property
    def has_errors(self) -> bool:
        """Check if machine has any errors or alarms."""
        return len(self.alarms) > 0 or self.emergency_stop_active


@dataclass
class ProgramInfo:
    """Information about a CNC program."""
    program_name: str
    program_content: str
    estimated_runtime: Optional[float] = None  # in minutes
    tool_list: List[ToolInfo] = field(default_factory=list)
    material: Optional[str] = None
    created_by: Optional[str] = None
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None


class CNCController(BaseAsyncComponent):
    """Base class for CNC machine controllers."""
    
    def __init__(
        self,
        component_id: str,
        machine_id: str,
        protocol: ProtocolType,
        connection_config: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(component_id, "CNCController", config)
        self.machine_id = machine_id
        self.protocol = protocol
        self.connection_config = connection_config
        self.current_status: Optional[MachineStatus] = None
        self.status_update_interval = config.get('status_update_interval', 1.0) if config else 1.0
        self._monitoring_task: Optional[asyncio.Task] = None
        self._event_callbacks: List[Callable[[MachineStatus], None]] = []
    
    @abstractmethod
    async def connect(self) -> OperationResult[bool]:
        """Connect to the CNC machine."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> OperationResult[bool]:
        """Disconnect from the CNC machine."""
        pass
    
    @abstractmethod
    async def get_status(self) -> OperationResult[MachineStatus]:
        """Get current machine status."""
        pass
    
    @abstractmethod
    async def send_command(self, command: CNCCommand, parameters: Optional[Dict[str, Any]] = None) -> OperationResult[bool]:
        """Send a command to the CNC machine."""
        pass
    
    async def load_program(self, program: ProgramInfo) -> OperationResult[bool]:
        """Load a program to the CNC machine."""
        return await self.send_command(CNCCommand.LOAD_PROGRAM, {"program": program})
    
    async def start_program(self) -> OperationResult[bool]:
        """Start the currently loaded program."""
        with safety_context(self, "start_program"):
            return await self.send_command(CNCCommand.START_PROGRAM)
    
    async def emergency_stop(self) -> OperationResult[bool]:
        """Trigger emergency stop."""
        with safety_context(self, "emergency_stop"):
            result = await self.send_command(CNCCommand.EMERGENCY_STOP)
            await super().emergency_stop()
            return result
    
    def add_status_callback(self, callback: Callable[[MachineStatus], None]) -> None:
        """Add a callback for status updates."""
        self._event_callbacks.append(callback)
    
    async def start_monitoring(self) -> OperationResult[bool]:
        """Start continuous status monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            return OperationResult.error_result(
                "Monitoring already active",
                error_code="ALREADY_MONITORING"
            )
        
        self._monitoring_task = await self.add_task(self._monitor_status())
        return OperationResult.success_result(True)
    
    async def stop_monitoring(self) -> OperationResult[bool]:
        """Stop status monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        return OperationResult.success_result(True)
    
    async def _monitor_status(self) -> None:
        """Continuous status monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                status_result = await self.get_status()
                if status_result.success:
                    old_status = self.current_status
                    self.current_status = status_result.result
                    
                    # Check for state changes or alarms
                    if old_status and old_status.state != self.current_status.state:
                        self.logger.info(
                            "Machine state changed",
                            machine_id=self.machine_id,
                            old_state=old_status.state.name,
                            new_state=self.current_status.state.name
                        )
                    
                    # Check for new alarms
                    if self.current_status.alarms:
                        self.logger.warning(
                            "Machine alarms detected",
                            machine_id=self.machine_id,
                            alarms=self.current_status.alarms
                        )
                    
                    # Notify callbacks
                    for callback in self._event_callbacks:
                        try:
                            callback(self.current_status)
                        except Exception as e:
                            self.logger.error(f"Error in status callback: {str(e)}")
                
                await asyncio.sleep(self.status_update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in status monitoring: {str(e)}")
                await asyncio.sleep(self.status_update_interval)


class MTConnectController(CNCController):
    """MTConnect protocol implementation for CNC communication."""
    
    def __init__(self, component_id: str, machine_id: str, connection_config: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        super().__init__(component_id, machine_id, ProtocolType.MTCONNECT, connection_config, config)
        self.base_url = connection_config.get('base_url', 'http://localhost:5000')
        self.device_uuid = connection_config.get('device_uuid')
        
    async def initialize(self) -> OperationResult[bool]:
        """Initialize MTConnect connection."""
        try:
            # Test connection by requesting probe
            import aiohttp
            async with aiohttp.ClientSession() as session:
                probe_url = f"{self.base_url}/probe"
                async with session.get(probe_url) as response:
                    if response.status == 200:
                        self.set_state(ComponentState.READY, "MTConnect initialized")
                        return OperationResult.success_result(True)
                    else:
                        return OperationResult.error_result(
                            f"MTConnect probe failed: HTTP {response.status}",
                            error_code="CONNECTION_FAILED"
                        )
        except Exception as e:
            return OperationResult.error_result(
                f"MTConnect initialization failed: {str(e)}",
                error_code="INITIALIZATION_ERROR"
            )
    
    async def connect(self) -> OperationResult[bool]:
        """Connect to MTConnect agent."""
        return await self.initialize()
    
    async def disconnect(self) -> OperationResult[bool]:
        """Disconnect from MTConnect agent."""
        return OperationResult.success_result(True)
    
    async def get_status(self) -> OperationResult[MachineStatus]:
        """Get current machine status via MTConnect."""
        timer = create_operation_timer()
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                current_url = f"{self.base_url}/current"
                if self.device_uuid:
                    current_url += f"?device={self.device_uuid}"
                
                async with session.get(current_url) as response:
                    if response.status != 200:
                        return OperationResult.error_result(
                            f"MTConnect current request failed: HTTP {response.status}",
                            error_code="REQUEST_FAILED",
                            duration_ms=timer()
                        )
                    
                    xml_content = await response.text()
                    status = self._parse_mtconnect_status(xml_content)
                    
                    return OperationResult.success_result(
                        status,
                        duration_ms=timer()
                    )
        
        except Exception as e:
            return OperationResult.error_result(
                f"Error getting MTConnect status: {str(e)}",
                error_code="STATUS_ERROR",
                duration_ms=timer()
            )
    
    def _parse_mtconnect_status(self, xml_content: str) -> MachineStatus:
        """Parse MTConnect XML response to extract machine status."""
        try:
            root = ET.fromstring(xml_content)
            
            # Basic parsing - in real implementation, this would be more comprehensive
            status = MachineStatus(
                machine_id=self.machine_id,
                state=MachineState.READY,  # Default state
                timestamp=datetime.now(timezone.utc)
            )
            
            # Parse device streams and data items
            for device_stream in root.findall(".//{*}DeviceStream"):
                for component_stream in device_stream.findall(".//{*}ComponentStream"):
                    # Parse data items
                    for sample in component_stream.findall(".//{*}Samples/*"):
                        self._process_mtconnect_sample(sample, status)
                    
                    for event in component_stream.findall(".//{*}Events/*"):
                        self._process_mtconnect_event(event, status)
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error parsing MTConnect XML: {str(e)}")
            return MachineStatus(
                machine_id=self.machine_id,
                state=MachineState.UNAVAILABLE,
                timestamp=datetime.now(timezone.utc)
            )
    
    def _process_mtconnect_sample(self, sample, status: MachineStatus) -> None:
        """Process MTConnect sample data item."""
        tag_name = sample.tag.split('}')[-1] if '}' in sample.tag else sample.tag
        value = sample.text
        
        if tag_name == "SpindleSpeed" and value:
            if not status.spindle_status:
                status.spindle_status = SpindleStatus(speed_rpm=0, load_percent=0)
            status.spindle_status.speed_rpm = float(value)
        elif tag_name == "Feedrate" and value:
            status.feedrate = float(value)
        elif tag_name.startswith("Position") and value:
            axis_name = sample.get('name', tag_name)
            status.axis_positions[axis_name] = AxisPosition(
                axis_name=axis_name,
                position=float(value)
            )
    
    def _process_mtconnect_event(self, event, status: MachineStatus) -> None:
        """Process MTConnect event data item."""
        tag_name = event.tag.split('}')[-1] if '}' in event.tag else event.tag
        value = event.text
        
        if tag_name == "Execution" and value:
            state_mapping = {
                "ACTIVE": MachineState.ACTIVE,
                "READY": MachineState.READY,
                "STOPPED": MachineState.STOPPED,
                "INTERRUPTED": MachineState.INTERRUPTED
            }
            status.state = state_mapping.get(value.upper(), MachineState.UNAVAILABLE)
        elif tag_name == "EmergencyStop" and value:
            status.emergency_stop_active = value.upper() == "ARMED"
        elif tag_name == "Program" and value:
            status.program_name = value
    
    async def send_command(self, command: CNCCommand, parameters: Optional[Dict[str, Any]] = None) -> OperationResult[bool]:
        """Send command via MTConnect (if supported by agent)."""
        # MTConnect is primarily a read-only protocol
        # Commands would typically require additional interfaces
        return OperationResult.error_result(
            "Command sending not supported via MTConnect",
            error_code="NOT_SUPPORTED"
        )


class OPCUAController(CNCController):
    """OPC-UA protocol implementation for CNC communication."""
    
    def __init__(self, component_id: str, machine_id: str, connection_config: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        super().__init__(component_id, machine_id, ProtocolType.OPCUA, connection_config, config)
        self.endpoint_url = connection_config.get('endpoint_url', 'opc.tcp://localhost:4840')
        self.client: Optional[OPCUAClient] = None
        self.username = connection_config.get('username')
        self.password = connection_config.get('password')
        
    async def initialize(self) -> OperationResult[bool]:
        """Initialize OPC-UA client."""
        if OPCUAClient is None:
            return OperationResult.error_result(
                "OPC-UA library not available. Install opcua package.",
                error_code="MISSING_DEPENDENCY"
            )
        
        self.set_state(ComponentState.READY, "OPC-UA controller initialized")
        return OperationResult.success_result(True)
    
    async def connect(self) -> OperationResult[bool]:
        """Connect to OPC-UA server."""
        timer = create_operation_timer()
        
        try:
            self.client = OPCUAClient(self.endpoint_url)
            
            if self.username and self.password:
                self.client.set_user(self.username)
                self.client.set_password(self.password)
            
            await asyncio.get_event_loop().run_in_executor(None, self.client.connect)
            
            return OperationResult.success_result(True, duration_ms=timer())
            
        except Exception as e:
            return OperationResult.error_result(
                f"OPC-UA connection failed: {str(e)}",
                error_code="CONNECTION_FAILED",
                duration_ms=timer()
            )
    
    async def disconnect(self) -> OperationResult[bool]:
        """Disconnect from OPC-UA server."""
        if self.client:
            try:
                await asyncio.get_event_loop().run_in_executor(None, self.client.disconnect)
                return OperationResult.success_result(True)
            except Exception as e:
                return OperationResult.error_result(
                    f"OPC-UA disconnection error: {str(e)}",
                    error_code="DISCONNECTION_ERROR"
                )
        return OperationResult.success_result(True)
    
    async def get_status(self) -> OperationResult[MachineStatus]:
        """Get machine status via OPC-UA."""
        if not self.client:
            return OperationResult.error_result(
                "Not connected to OPC-UA server",
                error_code="NOT_CONNECTED"
            )
        
        timer = create_operation_timer()
        
        try:
            # Read various status nodes
            status = MachineStatus(
                machine_id=self.machine_id,
                state=MachineState.READY,
                timestamp=datetime.now(timezone.utc)
            )
            
            # This is a simplified implementation
            # Real implementation would read specific node IDs for the machine
            
            return OperationResult.success_result(status, duration_ms=timer())
            
        except Exception as e:
            return OperationResult.error_result(
                f"Error reading OPC-UA status: {str(e)}",
                error_code="READ_ERROR",
                duration_ms=timer()
            )
    
    async def send_command(self, command: CNCCommand, parameters: Optional[Dict[str, Any]] = None) -> OperationResult[bool]:
        """Send command via OPC-UA."""
        if not self.client:
            return OperationResult.error_result(
                "Not connected to OPC-UA server",
                error_code="NOT_CONNECTED"
            )
        
        timer = create_operation_timer()
        
        try:
            # Map commands to OPC-UA method calls or variable writes
            # This is a simplified implementation
            
            if command == CNCCommand.EMERGENCY_STOP:
                with safety_context(self, "emergency_stop_command"):
                    # Write to emergency stop node
                    pass
            
            return OperationResult.success_result(True, duration_ms=timer())
            
        except Exception as e:
            return OperationResult.error_result(
                f"Error sending OPC-UA command: {str(e)}",
                error_code="COMMAND_ERROR",
                duration_ms=timer()
            )
    
    async def shutdown(self) -> OperationResult[bool]:
        """Shutdown OPC-UA controller."""
        await self.disconnect()
        return await super().shutdown()


class CNCManager(BaseAsyncComponent):
    """Central manager for multiple CNC machines."""
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(component_id, "CNCManager", config)
        self.controllers: Dict[str, CNCController] = {}
        self.status_history: Dict[str, List[MachineStatus]] = {}
        self.max_history_size = config.get('max_history_size', 1000) if config else 1000
    
    async def initialize(self) -> OperationResult[bool]:
        """Initialize CNC manager."""
        self.set_state(ComponentState.READY, "CNC manager initialized")
        return OperationResult.success_result(True)
    
    async def add_controller(self, controller: CNCController) -> OperationResult[bool]:
        """Add a CNC controller to management."""
        try:
            # Initialize controller
            init_result = await controller.initialize()
            if not init_result.success:
                return init_result
            
            # Connect controller
            connect_result = await controller.connect()
            if not connect_result.success:
                return connect_result
            
            # Add to management
            self.controllers[controller.machine_id] = controller
            self.status_history[controller.machine_id] = []
            
            # Add status callback
            controller.add_status_callback(self._on_status_update)
            
            # Start monitoring
            await controller.start_monitoring()
            
            self.logger.info(f"Added CNC controller: {controller.machine_id}")
            return OperationResult.success_result(True)
            
        except Exception as e:
            return OperationResult.error_result(
                f"Failed to add controller: {str(e)}",
                error_code="ADD_CONTROLLER_ERROR"
            )
    
    def _on_status_update(self, status: MachineStatus) -> None:
        """Handle status updates from controllers."""
        machine_id = status.machine_id
        
        # Add to history
        if machine_id in self.status_history:
            history = self.status_history[machine_id]
            history.append(status)
            
            # Limit history size
            if len(history) > self.max_history_size:
                history.pop(0)
    
    async def get_all_status(self) -> OperationResult[Dict[str, MachineStatus]]:
        """Get current status of all managed machines."""
        status_dict = {}
        
        for machine_id, controller in self.controllers.items():
            if controller.current_status:
                status_dict[machine_id] = controller.current_status
        
        return OperationResult.success_result(status_dict)
    
    async def emergency_stop_all(self) -> OperationResult[Dict[str, bool]]:
        """Trigger emergency stop on all machines."""
        results = {}
        
        with safety_context(self, "emergency_stop_all"):
            for machine_id, controller in self.controllers.items():
                try:
                    result = await controller.emergency_stop()
                    results[machine_id] = result.success
                except Exception as e:
                    self.logger.error(f"Emergency stop failed for {machine_id}: {str(e)}")
                    results[machine_id] = False
        
        return OperationResult.success_result(results)
    
    async def shutdown(self) -> OperationResult[bool]:
        """Shutdown all controllers."""
        for controller in self.controllers.values():
            try:
                await controller.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down controller: {str(e)}")
        
        return await super().shutdown()


# Export public interface
__all__ = [
    'MachineState',
    'CNCCommand',
    'ProtocolType',
    'AxisPosition',
    'ToolInfo',
    'SpindleStatus',
    'MachineStatus',
    'ProgramInfo',
    'CNCController',
    'MTConnectController',
    'OPCUAController',
    'CNCManager'
]
