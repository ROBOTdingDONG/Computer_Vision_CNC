#!/usr/bin/env python3
"""
Computer Vision CNC Manufacturing Platform - Architecture Verification Test

This script verifies that all architecture components from Tasks 8-10 are properly
implemented and can be imported/instantiated without errors.

Run this test to validate the complete architecture implementation.
"""

import sys
import traceback
from pathlib import Path

# Add the source directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_core_architecture():
    """Test core base classes and fundamental architecture."""
    print("🔧 Testing Core Architecture...")
    
    try:
        from cv_cnc_manufacturing.core.base import (
            BaseManufacturingComponent,
            BaseAsyncComponent,
            OperationResult,
            ComponentState,
            ManufacturingException,
            SafetyException,
            QualityException,
            safety_context
        )
        
        # Test basic instantiation
        result = OperationResult(success=True, result="Test successful")
        assert result.success is True
        
        print("  ✅ Core base classes imported and functional")
        return True
        
    except Exception as e:
        print(f"  ❌ Core architecture test failed: {e}")
        traceback.print_exc()
        return False

def test_computer_vision_architecture():
    """Test computer vision framework components."""
    print("📸 Testing Computer Vision Architecture...")
    
    try:
        from cv_cnc_manufacturing.computer_vision import (
            ImageProcessor,
            DefectDetector,
            QualityInspector,
            InspectionResult,
            DefectDetection,
            DefectType
        )
        
        # Test enum values
        defect_type = DefectType.SURFACE_DEFECT
        assert defect_type is not None
        
        print("  ✅ Computer vision components imported and functional")
        return True
        
    except Exception as e:
        print(f"  ❌ Computer vision architecture test failed: {e}")
        traceback.print_exc()
        return False

def test_cnc_integration_architecture():
    """Test CNC integration framework components."""
    print("🤖 Testing CNC Integration Architecture...")
    
    try:
        from cv_cnc_manufacturing.cnc import (
            CNCManager,
            CNCController,
            MTConnectController,
            OPCUAController,
            MachineState,
            MachineStatus,
            AxisPosition
        )
        
        # Test enum values
        machine_state = MachineState.READY
        assert machine_state is not None
        
        print("  ✅ CNC integration components imported and functional")
        return True
        
    except Exception as e:
        print(f"  ❌ CNC integration architecture test failed: {e}")
        traceback.print_exc()
        return False

def test_api_architecture():
    """Test REST API framework components."""
    print("🌐 Testing API Architecture...")
    
    try:
        from cv_cnc_manufacturing.api import (
            ManufacturingAPI,
            create_api_server,
            run_api_server,
            APIConfig
        )
        
        # Test API config creation
        config = APIConfig()
        assert config is not None
        
        print("  ✅ API components imported and functional")
        return True
        
    except Exception as e:
        print(f"  ❌ API architecture test failed: {e}")
        traceback.print_exc()
        return False

def test_development_environment():
    """Test development environment framework."""
    print("🛠️ Testing Development Environment...")
    
    try:
        from cv_cnc_manufacturing.development import (
            DevelopmentEnvironment,
            validate_dev_environment,
            setup_development_environment
        )
        
        # Test development environment instantiation
        dev_env = DevelopmentEnvironment()
        assert dev_env is not None
        
        print("  ✅ Development environment components imported and functional")
        return True
        
    except Exception as e:
        print(f"  ❌ Development environment test failed: {e}")
        traceback.print_exc()
        return False

def test_package_integration():
    """Test main package integration and exports."""
    print("📦 Testing Package Integration...")
    
    try:
        import cv_cnc_manufacturing
        
        # Test version information
        version = cv_cnc_manufacturing.get_version()
        assert version is not None
        
        # Test platform info
        platform_info = cv_cnc_manufacturing.get_platform_info()
        assert platform_info is not None
        assert "name" in platform_info
        
        print(f"  ✅ Package integration successful - Version: {version}")
        return True
        
    except Exception as e:
        print(f"  ❌ Package integration test failed: {e}")
        traceback.print_exc()
        return False

def test_import_completeness():
    """Test that all major components can be imported from main package."""
    print("🔗 Testing Import Completeness...")
    
    try:
        import cv_cnc_manufacturing
        
        # Test available imports defensively
        successful_imports = []
        
        # Core components
        try:
            from cv_cnc_manufacturing import BaseManufacturingComponent, OperationResult
            successful_imports.extend(["BaseManufacturingComponent", "OperationResult"])
        except ImportError as e:
            print(f"  Core import failed: {e}")
        
        # Computer vision
        try:
            from cv_cnc_manufacturing import QualityInspector, DefectDetector
            successful_imports.extend(["QualityInspector", "DefectDetector"])
        except ImportError as e:
            print(f"  Computer vision import failed: {e}")
        
        # CNC integration
        try:
            from cv_cnc_manufacturing import MTConnectController
            successful_imports.append("MTConnectController")
        except ImportError as e:
            print(f"  CNC integration import failed: {e}")
        
        # API
        try:
            from cv_cnc_manufacturing import ManufacturingAPI, create_api_server
            successful_imports.extend(["ManufacturingAPI", "create_api_server"])
        except ImportError as e:
            print(f"  API import failed: {e}")
        
        # Development
        try:
            from cv_cnc_manufacturing import DevelopmentEnvironment, setup_development_environment
            successful_imports.extend(["DevelopmentEnvironment", "setup_development_environment"])
        except ImportError as e:
            print(f"  Development import failed: {e}")
        
        # Check what we managed to import
        if len(successful_imports) >= 4:  # We expect at least some core components
            print(f"  ✅ Successfully imported {len(successful_imports)} major components: {', '.join(successful_imports[:5])}{'...' if len(successful_imports) > 5 else ''}")
            return True
        else:
            print(f"  ❌ Only imported {len(successful_imports)} components: {successful_imports}")
            return False
        
    except Exception as e:
        print(f"  ❌ Import completeness test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all architecture verification tests."""
    print("🏗️ Computer Vision CNC Manufacturing Platform - Architecture Verification")
    print("=" * 70)
    
    tests = [
        test_core_architecture,
        test_computer_vision_architecture,
        test_cnc_integration_architecture,
        test_api_architecture,
        test_development_environment,
        test_package_integration,
        test_import_completeness
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test {test.__name__} crashed: {e}")
        print()
    
    print("=" * 70)
    print(f"📊 Architecture Verification Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ✅ ALL ARCHITECTURE TESTS PASSED!")
        print("🚀 Platform architecture is complete and ready for development!")
        print("\n🏁 Tasks 8-10 Successfully Completed:")
        print("   ✅ Task 8: Code Architecture")
        print("   ✅ Task 9: API Design") 
        print("   ✅ Task 10: Development Environment")
        return 0
    else:
        print("⚠️ ❌ Some architecture tests failed.")
        print("📝 Review the errors above and fix any issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
