"""
Computer Vision core architecture for CNC Manufacturing Platform.

This module provides the foundational computer vision components including
image processing, defect detection, quality inspection, and measurement systems.

Safety Notice: Computer vision results should always be validated against
physical measurements and safety systems before making manufacturing decisions.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union, NamedTuple
import numpy as np
from datetime import datetime, timezone

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import torch
    import torchvision.transforms as transforms
except ImportError:
    torch = None
    transforms = None

from ..core.base import (
    BaseAsyncComponent, 
    OperationResult, 
    ComponentState,
    ManufacturingException,
    QualityException,
    safety_context,
    create_operation_timer
)


class InspectionResult(Enum):
    """Quality inspection results."""
    PASS = auto()
    FAIL = auto()
    UNCERTAIN = auto()
    NEEDS_REVIEW = auto()


class DefectType(Enum):
    """Types of manufacturing defects that can be detected."""
    SURFACE_DEFECT = "surface_defect"
    DIMENSIONAL_ERROR = "dimensional_error"
    SCRATCH = "scratch"
    CRACK = "crack"
    DISCOLORATION = "discoloration"
    FOREIGN_MATERIAL = "foreign_material"
    INCOMPLETE_FEATURE = "incomplete_feature"
    BURR = "burr"
    CORROSION = "corrosion"
    DEFORMATION = "deformation"
    UNKNOWN = "unknown"


@dataclass
class ImageMetadata:
    """Metadata for manufacturing images."""
    width: int
    height: int
    channels: int
    bit_depth: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    camera_id: Optional[str] = None
    lighting_conditions: Optional[str] = None
    magnification: Optional[float] = None
    pixel_size_um: Optional[float] = None  # Micrometers per pixel
    part_id: Optional[str] = None
    lot_number: Optional[str] = None
    operator: Optional[str] = None


@dataclass
class BoundingBox:
    """Bounding box for detected objects or defects."""
    x: float
    y: float
    width: float
    height: float
    confidence: float = 0.0
    
    @property
    def center(self) -> Tuple[float, float]:
        """Get center coordinates of bounding box."""
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def area(self) -> float:
        """Get area of bounding box."""
        return self.width * self.height


@dataclass
class DefectDetection:
    """Detected defect information."""
    defect_type: DefectType
    confidence: float
    bounding_box: BoundingBox
    severity: float  # 0.0 to 1.0
    description: Optional[str] = None
    location_description: Optional[str] = None
    recommended_action: Optional[str] = None
    detection_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class QualityMeasurement:
    """Quality measurement result."""
    measurement_type: str
    value: float
    unit: str
    tolerance_min: Optional[float] = None
    tolerance_max: Optional[float] = None
    within_tolerance: bool = True
    confidence: float = 1.0
    measurement_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate measurement against tolerances."""
        if self.tolerance_min is not None and self.tolerance_max is not None:
            self.within_tolerance = self.tolerance_min <= self.value <= self.tolerance_max


@dataclass
class InspectionReport:
    """Comprehensive quality inspection report."""
    part_id: str
    inspection_result: InspectionResult
    overall_score: float  # 0.0 to 1.0
    defects: List[DefectDetection] = field(default_factory=list)
    measurements: List[QualityMeasurement] = field(default_factory=list)
    processing_time_ms: float = 0.0
    inspector_notes: Optional[str] = None
    inspection_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def defect_count(self) -> int:
        """Get total number of defects detected."""
        return len(self.defects)
    
    @property
    def critical_defects(self) -> List[DefectDetection]:
        """Get list of critical defects (severity > 0.7)."""
        return [d for d in self.defects if d.severity > 0.7]
    
    @property
    def out_of_tolerance_measurements(self) -> List[QualityMeasurement]:
        """Get measurements that are out of tolerance."""
        return [m for m in self.measurements if not m.within_tolerance]


class ImageProcessor(BaseAsyncComponent):
    """Base class for image processing components."""
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(component_id, "ImageProcessor", config)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
    async def initialize(self) -> OperationResult[bool]:
        """Initialize image processor."""
        if cv2 is None:
            return OperationResult.error_result(
                "OpenCV not available. Install opencv-python package.",
                error_code="MISSING_DEPENDENCY"
            )
        
        self.set_state(ComponentState.READY, "Image processor initialized")
        return OperationResult.success_result(True)
    
    async def load_image(self, image_path: str) -> OperationResult[Tuple[np.ndarray, ImageMetadata]]:
        """Load and validate image from file."""
        timer = create_operation_timer()
        
        try:
            # Validate file format
            import pathlib
            if pathlib.Path(image_path).suffix.lower() not in self.supported_formats:
                return OperationResult.error_result(
                    f"Unsupported image format: {image_path}",
                    error_code="UNSUPPORTED_FORMAT",
                    duration_ms=timer()
                )
            
            # Load image
            image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if image is None:
                return OperationResult.error_result(
                    f"Failed to load image: {image_path}",
                    error_code="LOAD_FAILED",
                    duration_ms=timer()
                )
            
            # Create metadata
            height, width, channels = image.shape
            metadata = ImageMetadata(
                width=width,
                height=height,
                channels=channels,
                bit_depth=8  # Assuming 8-bit per channel
            )
            
            return OperationResult.success_result(
                (image, metadata),
                duration_ms=timer()
            )
            
        except Exception as e:
            return OperationResult.error_result(
                f"Error loading image: {str(e)}",
                error_code="PROCESSING_ERROR",
                duration_ms=timer()
            )
    
    async def preprocess_image(self, image: np.ndarray) -> OperationResult[np.ndarray]:
        """Apply standard preprocessing to image."""
        timer = create_operation_timer()
        
        try:
            # Basic preprocessing pipeline
            processed = image.copy()
            
            # Noise reduction
            processed = cv2.bilateralFilter(processed, 9, 75, 75)
            
            # Contrast enhancement
            lab = cv2.cvtColor(processed, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            processed = cv2.merge([l, a, b])
            processed = cv2.cvtColor(processed, cv2.COLOR_LAB2BGR)
            
            return OperationResult.success_result(
                processed,
                duration_ms=timer()
            )
            
        except Exception as e:
            return OperationResult.error_result(
                f"Error preprocessing image: {str(e)}",
                error_code="PREPROCESSING_ERROR",
                duration_ms=timer()
            )


class DefectDetector(BaseAsyncComponent):
    """AI-powered defect detection system."""
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(component_id, "DefectDetector", config)
        self.model = None
        self.confidence_threshold = config.get('confidence_threshold', 0.5) if config else 0.5
        self.nms_threshold = config.get('nms_threshold', 0.4) if config else 0.4
        
    async def initialize(self) -> OperationResult[bool]:
        """Initialize defect detection model."""
        try:
            # In a real implementation, load a trained model here
            # For now, we'll use traditional computer vision methods
            self.set_state(ComponentState.READY, "Defect detector initialized")
            return OperationResult.success_result(True)
            
        except Exception as e:
            return OperationResult.error_result(
                f"Failed to initialize defect detector: {str(e)}",
                error_code="INITIALIZATION_ERROR"
            )
    
    async def detect_defects(self, image: np.ndarray) -> OperationResult[List[DefectDetection]]:
        """Detect defects in the input image."""
        if self.state != ComponentState.READY:
            return OperationResult.error_result(
                "Defect detector not ready",
                error_code="COMPONENT_NOT_READY"
            )
        
        timer = create_operation_timer()
        
        with safety_context(self, "defect_detection"):
            try:
                defects = []
                
                # Convert to grayscale for analysis
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # Edge detection for cracks and scratches
                edges = cv2.Canny(gray, 50, 150)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    if cv2.contourArea(contour) > 100:  # Filter small contours
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # Classify defect type based on shape characteristics
                        aspect_ratio = w / h
                        if aspect_ratio > 3:  # Long thin defects might be scratches
                            defect_type = DefectType.SCRATCH
                        else:
                            defect_type = DefectType.SURFACE_DEFECT
                        
                        # Calculate confidence and severity
                        area = cv2.contourArea(contour)
                        confidence = min(0.9, area / 1000.0)  # Simple confidence calculation
                        severity = min(1.0, area / 5000.0)  # Simple severity calculation
                        
                        if confidence >= self.confidence_threshold:
                            defect = DefectDetection(
                                defect_type=defect_type,
                                confidence=confidence,
                                bounding_box=BoundingBox(x, y, w, h, confidence),
                                severity=severity,
                                description=f"Detected {defect_type.value} with area {area:.1f} pixels"
                            )
                            defects.append(defect)
                
                return OperationResult.success_result(
                    defects,
                    duration_ms=timer(),
                    metadata={"total_contours": len(contours), "filtered_defects": len(defects)}
                )
                
            except Exception as e:
                return OperationResult.error_result(
                    f"Error detecting defects: {str(e)}",
                    error_code="DETECTION_ERROR",
                    duration_ms=timer()
                )


class QualityInspector(BaseAsyncComponent):
    """Comprehensive quality inspection system."""
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(component_id, "QualityInspector", config)
        self.image_processor = ImageProcessor(f"{component_id}_processor", config)
        self.defect_detector = DefectDetector(f"{component_id}_detector", config)
        self.quality_thresholds = config.get('quality_thresholds', {}) if config else {}
        
    async def initialize(self) -> OperationResult[bool]:
        """Initialize quality inspection system."""
        try:
            # Initialize components
            processor_result = await self.image_processor.initialize()
            if not processor_result.success:
                return processor_result
            
            detector_result = await self.defect_detector.initialize()
            if not detector_result.success:
                return detector_result
            
            self.set_state(ComponentState.READY, "Quality inspector initialized")
            return OperationResult.success_result(True)
            
        except Exception as e:
            return OperationResult.error_result(
                f"Failed to initialize quality inspector: {str(e)}",
                error_code="INITIALIZATION_ERROR"
            )
    
    async def inspect_part(
        self,
        image: np.ndarray,
        part_id: str,
        metadata: Optional[ImageMetadata] = None
    ) -> OperationResult[InspectionReport]:
        """Perform comprehensive quality inspection on a part."""
        if self.state != ComponentState.READY:
            return OperationResult.error_result(
                "Quality inspector not ready",
                error_code="COMPONENT_NOT_READY"
            )
        
        timer = create_operation_timer()
        
        with safety_context(self, "quality_inspection"):
            try:
                # Preprocess image
                preprocess_result = await self.image_processor.preprocess_image(image)
                if not preprocess_result.success:
                    return OperationResult.error_result(
                        f"Preprocessing failed: {preprocess_result.error}",
                        error_code="PREPROCESSING_FAILED",
                        duration_ms=timer()
                    )
                
                processed_image = preprocess_result.result
                
                # Detect defects
                defect_result = await self.defect_detector.detect_defects(processed_image)
                if not defect_result.success:
                    return OperationResult.error_result(
                        f"Defect detection failed: {defect_result.error}",
                        error_code="DEFECT_DETECTION_FAILED",
                        duration_ms=timer()
                    )
                
                defects = defect_result.result
                
                # Perform measurements (simplified)
                measurements = await self._perform_measurements(processed_image)
                
                # Calculate overall quality score
                overall_score = self._calculate_quality_score(defects, measurements)
                
                # Determine inspection result
                inspection_result = self._determine_inspection_result(overall_score, defects, measurements)
                
                # Create inspection report
                report = InspectionReport(
                    part_id=part_id,
                    inspection_result=inspection_result,
                    overall_score=overall_score,
                    defects=defects,
                    measurements=measurements,
                    processing_time_ms=timer()
                )
                
                return OperationResult.success_result(
                    report,
                    duration_ms=timer(),
                    metadata={
                        "defect_count": len(defects),
                        "measurement_count": len(measurements),
                        "overall_score": overall_score
                    }
                )
                
            except Exception as e:
                return OperationResult.error_result(
                    f"Error during inspection: {str(e)}",
                    error_code="INSPECTION_ERROR",
                    duration_ms=timer()
                )
    
    async def _perform_measurements(self, image: np.ndarray) -> List[QualityMeasurement]:
        """Perform dimensional and surface measurements."""
        measurements = []
        
        try:
            # Example measurement: surface roughness estimation
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            roughness = np.std(gray.astype(float))
            
            measurements.append(QualityMeasurement(
                measurement_type="surface_roughness",
                value=roughness,
                unit="pixel_intensity_std",
                tolerance_min=0.0,
                tolerance_max=50.0,
                confidence=0.8
            ))
            
            # Example measurement: overall brightness
            brightness = np.mean(gray)
            measurements.append(QualityMeasurement(
                measurement_type="brightness",
                value=brightness,
                unit="pixel_intensity_mean",
                tolerance_min=80.0,
                tolerance_max=200.0,
                confidence=0.9
            ))
            
        except Exception as e:
            self.logger.warning(f"Error performing measurements: {str(e)}")
        
        return measurements
    
    def _calculate_quality_score(
        self,
        defects: List[DefectDetection],
        measurements: List[QualityMeasurement]
    ) -> float:
        """Calculate overall quality score (0.0 to 1.0)."""
        score = 1.0
        
        # Penalize for defects
        for defect in defects:
            penalty = defect.severity * defect.confidence * 0.2
            score -= penalty
        
        # Penalize for out-of-tolerance measurements
        for measurement in measurements:
            if not measurement.within_tolerance:
                penalty = 0.1 * measurement.confidence
                score -= penalty
        
        return max(0.0, min(1.0, score))
    
    def _determine_inspection_result(
        self,
        overall_score: float,
        defects: List[DefectDetection],
        measurements: List[QualityMeasurement]
    ) -> InspectionResult:
        """Determine final inspection result."""
        # Check for critical defects
        critical_defects = [d for d in defects if d.severity > 0.7]
        if critical_defects:
            return InspectionResult.FAIL
        
        # Check for out-of-tolerance measurements
        out_of_tolerance = [m for m in measurements if not m.within_tolerance]
        if out_of_tolerance:
            return InspectionResult.FAIL
        
        # Score-based determination
        if overall_score >= 0.95:
            return InspectionResult.PASS
        elif overall_score >= 0.8:
            return InspectionResult.NEEDS_REVIEW
        elif overall_score >= 0.6:
            return InspectionResult.UNCERTAIN
        else:
            return InspectionResult.FAIL
    
    async def shutdown(self) -> OperationResult[bool]:
        """Shutdown quality inspector and all components."""
        try:
            await self.image_processor.shutdown()
            await self.defect_detector.shutdown()
            return await super().shutdown()
        except Exception as e:
            return OperationResult.error_result(
                f"Error during shutdown: {str(e)}",
                error_code="SHUTDOWN_ERROR"
            )


# Export public interface
__all__ = [
    'InspectionResult',
    'DefectType',
    'ImageMetadata',
    'BoundingBox',
    'DefectDetection',
    'QualityMeasurement',
    'InspectionReport',
    'ImageProcessor',
    'DefectDetector',
    'QualityInspector'
]
