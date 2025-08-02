# Computer Vision CNC Manufacturing Platform - Testing Guide

This guide provides comprehensive testing procedures to ensure the platform works properly across all manufacturing scenarios.

## 🧪 Testing Strategy Overview

### Testing Levels
1. **Unit Tests** - Individual component testing
2. **Integration Tests** - System component interaction testing
3. **Performance Tests** - Latency and throughput validation
4. **Security Tests** - IEC 62443 compliance validation
5. **Compliance Tests** - Manufacturing standards verification
6. **End-to-End Tests** - Complete workflow validation

### Manufacturing-Specific Testing
- **CNC Integration Testing** - Machine connectivity and protocol validation
- **Computer Vision Testing** - Accuracy and latency benchmarks
- **Quality Control Testing** - Statistical process control validation
- **Safety System Testing** - Emergency stop and safety interlocks
- **Compliance Testing** - ISO 9001, IATF 16949, IEC 62443 validation

## 🚀 Quick Start Testing

### 1. Environment Validation
```bash
# Validate complete environment
python setup.py --validate-only

# Check all dependencies
make dependencies-check

# Validate system requirements
make system-info
```

### 2. Basic Installation Test
```bash
# Install in development mode
make install-dev

# Verify installation
python -c "import cv_cnc_manufacturing; print(cv_cnc_manufacturing.get_version())"

# Check package integrity
python -c "from cv_cnc_manufacturing import get_platform_info; print(get_platform_info())"
```

### 3. Core Functionality Tests
```bash
# Run unit tests
make test-unit

# Run integration tests  
make test-integration

# Run manufacturing-specific tests
make test-manufacturing
```

## 🔧 Detailed Testing Procedures

### Unit Testing
```bash
# Run all unit tests with coverage
pytest tests/unit/ -v --cov=src --cov-report=html

# Test specific components
pytest tests/unit/test_computer_vision.py -v
pytest tests/unit/test_quality_control.py -v
pytest tests/unit/test_cnc_integration.py -v

# Test with manufacturing markers
pytest -m "unit and manufacturing" -v
```

### Integration Testing
```bash
# Full integration test suite
pytest tests/integration/ -v --tb=short

# CNC integration tests (requires mock CNC or simulator)
pytest tests/integration/test_cnc_integrations.py -v

# Database integration tests
pytest tests/integration/test_database_integration.py -v

# API integration tests
pytest tests/integration/test_api_integration.py -v
```

### Performance Testing
```bash
# Run performance benchmarks
make benchmark

# Computer vision performance tests
pytest tests/performance/test_cv_performance.py --benchmark-only

# Load testing (requires running services)
make load-test

# Stress testing
make stress-test
```

### Security Testing
```bash
# Security vulnerability scanning
make security-scan

# Run security tests
make test-security

# Compliance validation
make compliance-validate

# Certificate validation
make certificates-generate
```

## 🏭 Manufacturing Environment Testing

### CNC Machine Integration Testing

#### 1. Protocol Testing
```bash
# Test MTConnect connectivity
python -m cv_cnc_manufacturing.cnc.test_mtconnect --host localhost --port 5000

# Test OPC-UA connectivity  
python -m cv_cnc_manufacturing.cnc.test_opcua --endpoint opc.tcp://localhost:4840

# Test Modbus connectivity
python -m cv_cnc_manufacturing.cnc.test_modbus --host 192.168.1.100 --port 502
```

#### 2. Mock CNC Testing
```bash
# Start mock CNC services
docker-compose -f docker-compose.test.yml up cnc-simulator

# Run CNC integration tests against simulator
pytest tests/integration/test_cnc_integrations.py --cnc-simulator
```

### Computer Vision Testing

#### 1. Accuracy Validation
```bash
# Test computer vision accuracy with sample images
python -m cv_cnc_manufacturing.computer_vision.test_accuracy --dataset tests/data/sample_images/

# Benchmark processing latency
python -m cv_cnc_manufacturing.computer_vision.benchmark_latency --iterations 1000

# Test quality inspection accuracy
pytest tests/unit/test_computer_vision.py::TestQualityInspection::test_defect_detection_accuracy
```

#### 2. Camera Integration Testing
```bash
# Test camera connectivity (requires cameras or simulators)
python -m cv_cnc_manufacturing.computer_vision.test_cameras --list-cameras

# Test image processing pipeline
pytest tests/integration/test_camera_integration.py -v
```

### Quality Control Testing

#### 1. Statistical Process Control
```bash
# Test SPC calculations
pytest tests/unit/test_quality_control.py::TestStatisticalProcessControl -v

# Validate measurement accuracy
python -m cv_cnc_manufacturing.quality_control.validate_measurements --calibration-data tests/data/calibration/
```

#### 2. Compliance Testing
```bash
# ISO 9001 compliance validation
python -m cv_cnc_manufacturing.compliance.validate_iso9001

# IATF 16949 automotive compliance
python -m cv_cnc_manufacturing.compliance.validate_iatf16949

# Export control compliance check
make export-control-check
```

## 🐳 Docker Environment Testing

### 1. Container Build Testing
```bash
# Build all container targets
docker build --target production -t cv-cnc-manufacturing:test .
docker build --target development -t cv-cnc-manufacturing:dev-test .
docker build --target testing -t cv-cnc-manufacturing:testing .

# Test container functionality
docker run --rm cv-cnc-manufacturing:test python -c "import cv_cnc_manufacturing; print('Container test passed')"
```

### 2. Docker Compose Testing
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run health checks
docker-compose -f docker-compose.test.yml ps

# Test service connectivity
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/status

# Cleanup test environment
docker-compose -f docker-compose.test.yml down -v
```

## 📊 Documentation Testing

### 1. Documentation Build Testing
```bash
# Test MkDocs build
mkdocs build --strict

# Serve documentation locally for testing
mkdocs serve

# Test documentation links
pytest tests/docs/test_documentation_links.py -v

# Validate API documentation
pytest tests/docs/test_api_documentation.py -v
```

### 2. Code Documentation Testing
```bash
# Test docstring coverage
pytest --doctest-modules src/cv_cnc_manufacturing/

# Generate API documentation
sphinx-build -b html docs/api/ docs/build/api/

# Test documentation examples
pytest docs/examples/ -v --doctest-glob="*.md"
```

## 🔍 Continuous Integration Testing

### 1. Pre-commit Testing
```bash
# Install and test pre-commit hooks
pre-commit install
pre-commit run --all-files

# Test code quality
make lint
make type-check
make format
```

### 2. CI Pipeline Testing
```bash
# Simulate CI environment locally
make ci-test

# Test release process
make release-check

# Validate packaging
python -m build
twine check dist/*
```

## 📈 Performance Benchmarking

### 1. Computer Vision Performance
```bash
# Benchmark image processing speed
python -m cv_cnc_manufacturing.benchmarks.cv_performance \
  --image-size 1920x1080 \
  --batch-size 16 \
  --iterations 1000

# Expected Results:
# - Processing time: <20ms per image
# - Throughput: >50 FPS
# - Memory usage: <2GB
# - GPU utilization: >80% (if available)
```

### 2. Database Performance
```bash
# Benchmark database operations
python -m cv_cnc_manufacturing.benchmarks.db_performance \
  --operations 10000 \
  --concurrent-connections 50

# Expected Results:
# - Insert rate: >1000 ops/sec
# - Query response: <10ms
# - Connection pool efficiency: >95%
```

### 3. API Performance
```bash
# Load test API endpoints
python -m cv_cnc_manufacturing.benchmarks.api_performance \
  --endpoint http://localhost:8000/api/v1/quality/inspect \
  --concurrent-users 100 \
  --duration 300

# Expected Results:
# - Response time: <100ms (95th percentile)
# - Throughput: >1000 requests/sec
# - Error rate: <0.1%
```

## 🛡️ Security Testing

### 1. Vulnerability Scanning
```bash
# Scan for security vulnerabilities
bandit -r src/ -f json -o security-report.json
safety check --json --output safety-report.json

# Container security scanning
docker run --rm -v $(pwd):/app clair-scanner cv-cnc-manufacturing:latest
```

### 2. Penetration Testing
```bash
# Network security testing
nmap -sS -O -A localhost

# Web application security testing
zap-baseline.py -t http://localhost:8000

# Industrial protocol security testing
python -m cv_cnc_manufacturing.security.test_protocol_security
```

## 🏥 Health Check Testing

### 1. System Health Validation
```bash
# Comprehensive health check
make health-check

# Individual service health checks
curl http://localhost:8000/health/database
curl http://localhost:8000/health/computer-vision
curl http://localhost:8000/health/cnc-integration
```

### 2. Monitoring System Testing
```bash
# Test metrics collection
curl http://localhost:9090/metrics

# Test alerting system
python -m cv_cnc_manufacturing.monitoring.test_alerts

# Validate log aggregation
python -m cv_cnc_manufacturing.monitoring.test_logging
```

## 🔧 Troubleshooting Testing Issues

### Common Issues and Solutions

#### 1. Import Errors
```bash
# If modules can't be imported
pip install -e .

# Verify PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Check package installation
pip list | grep cv-cnc-manufacturing
```

#### 2. Docker Issues
```bash
# Clear Docker cache
docker system prune -a

# Rebuild containers from scratch
docker-compose build --no-cache

# Check container logs
docker-compose logs cv-cnc-api-server
```

#### 3. Test Database Issues
```bash
# Reset test database
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d postgres

# Run database migrations
python -m cv_cnc_manufacturing.db.migrate --test-db
```

#### 4. Permission Issues (Windows)
```powershell
# Run PowerShell as Administrator for Docker operations
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Fix file permissions for certificates
icacls certs /grant Everyone:F /T
```

## 📋 Test Results Validation

### Success Criteria
- ✅ **Unit Tests**: >95% pass rate, >80% code coverage
- ✅ **Integration Tests**: 100% pass rate for critical paths
- ✅ **Performance Tests**: Meet latency requirements (<20ms CV processing)
- ✅ **Security Tests**: No high/critical vulnerabilities
- ✅ **Compliance Tests**: 100% compliance with manufacturing standards

### Reporting
```bash
# Generate comprehensive test report
pytest tests/ --html=reports/test_report.html --self-contained-html

# Generate coverage report
pytest --cov=src --cov-report=html:reports/coverage/

# Generate performance report
python -m cv_cnc_manufacturing.benchmarks.generate_report --output reports/performance/
```

---

*This testing guide ensures comprehensive validation of the Computer Vision CNC Manufacturing Platform across all critical manufacturing scenarios. Regular execution of these tests maintains system reliability and compliance.*
