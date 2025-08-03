# Computer Vision CNC Manufacturing Platform
# Multi-stage Docker build for production deployment
# Optimized for manufacturing environments with security and performance

# =============================================================================
# Base Image - Ubuntu LTS with industrial software support
# =============================================================================
FROM ubuntu:22.04 as base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install system dependencies for manufacturing environment
RUN apt-get update && apt-get install -y \
    # Core system tools
    curl \
    wget \
    git \
    build-essential \
    pkg-config \
    software-properties-common \
    # Python and development tools
    python3.10 \
    python3.10-dev \
    python3-pip \
    python3.10-venv \
    # Computer vision dependencies
    libopencv-dev \
    python3-opencv \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    # Industrial communication libraries
    libmodbus-dev \
    libssl-dev \
    libffi-dev \
    # Database and connectivity
    libpq-dev \
    postgresql-client \
    redis-tools \
    # Monitoring and debugging
    htop \
    nano \
    vim \
    strace \
    # Security tools
    openssl \
    ca-certificates \
    # Manufacturing-specific dependencies
    libudev-dev \
    libusb-1.0-0-dev \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Create application user for security
RUN groupadd -r cvcnc && useradd -r -g cvcnc cvcnc

# Create application directories
RUN mkdir -p /app \
             /app/src \
             /app/configs \
             /app/data \
             /app/logs \
             /app/certs \
             /app/temp \
             /app/compliance_reports \
    && chown -R cvcnc:cvcnc /app

# =============================================================================
# Development Stage - Additional development tools
# =============================================================================
FROM base as development

# Install additional development dependencies
RUN apt-get update && apt-get install -y \
    # Development tools
    python3-dev \
    gdb \
    valgrind \
    # Documentation tools
    pandoc \
    texlive-latex-base \
    # Testing tools
    python3-pytest \
    # Code quality tools
    python3-flake8 \
    # Manufacturing development tools
    can-utils \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set development environment
ENV ENVIRONMENT=development \
    DEBUG=true \
    LOG_LEVEL=DEBUG

# =============================================================================
# Python Dependencies Stage - Optimized dependency installation
# =============================================================================
FROM base as python-deps

# Upgrade pip and install build tools
RUN python3 -m pip install --upgrade pip setuptools wheel

# Copy requirements files
COPY requirements.txt requirements-dev.txt requirements-compliance.txt /tmp/

# Install Python dependencies
RUN python3 -m pip install -r /tmp/requirements.txt && \
    python3 -m pip install -r /tmp/requirements-compliance.txt && \
    # Clean pip cache
    python3 -m pip cache purge

# =============================================================================
# Production Base - Optimized for manufacturing deployment
# =============================================================================
FROM base as production-base

# Copy Python dependencies from previous stage
COPY --from=python-deps /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Set production environment variables
ENV ENVIRONMENT=production \
    DEBUG=false \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app/src \
    PATH=/usr/local/bin:$PATH

# Security hardening
RUN apt-get autoremove -y && \
    # Secure file permissions
    chmod 750 /app && \
    # Remove shell history and temporary files
    rm -f /root/.bash_history && \
    rm -rf /tmp/* /var/tmp/* && \
    # Update security certificates
    update-ca-certificates

# =============================================================================
# Application Stage - Application code and configuration
# =============================================================================
FROM production-base as application

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=cvcnc:cvcnc src/ /app/src/
COPY --chown=cvcnc:cvcnc configs/ /app/configs/
COPY --chown=cvcnc:cvcnc pyproject.toml setup.py /app/

# Copy additional configuration files
COPY --chown=cvcnc:cvcnc .env.example /app/.env.example
COPY --chown=cvcnc:cvcnc LICENSE /app/LICENSE
COPY --chown=cvcnc:cvcnc README.md /app/README.md

# Install application in development mode for easier updates
RUN python3 -m pip install -e . && \
    python3 -m pip cache purge

# Create necessary runtime directories
RUN mkdir -p /app/logs /app/data/models /app/data/images /app/temp && \
    chown -R cvcnc:cvcnc /app/logs /app/data /app/temp

# =============================================================================
# Production Stage - Final optimized image
# =============================================================================
FROM application as production

# Switch to non-root user
USER cvcnc

# Expose application ports
EXPOSE 8000 8001 8080

# Health check for manufacturing systems
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Manufacturing-specific labels for container management
LABEL org.opencontainers.image.title="CV CNC Manufacturing Platform" \
      org.opencontainers.image.description="Computer Vision CNC Manufacturing Optimization Platform" \
      org.opencontainers.image.vendor="CV CNC Platform Team" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-01-XX" \
      manufacturing.compliance.iso9001="true" \
      manufacturing.compliance.iatf16949="true" \
      manufacturing.compliance.iec62443="true" \
      manufacturing.protocols.mtconnect="true" \
      manufacturing.protocols.opcua="true" \
      security.scanning="required" \
      deployment.environment="production"

# Default command - can be overridden for different services
CMD ["python3", "-m", "cv_cnc_manufacturing.api.server"]

# =============================================================================
# Development Stage - Development-specific optimizations
# =============================================================================
FROM development as dev

# Copy development dependencies
COPY --from=python-deps /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy all application files for development
COPY --chown=cvcnc:cvcnc . /app/

# Install application and development dependencies
RUN python3 -m pip install -e .[dev,test,docs] && \
    python3 -m pip cache purge

# Install pre-commit hooks
RUN pre-commit install --install-hooks

# Switch to development user
USER cvcnc

# Development-specific health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=2 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose additional development ports
EXPOSE 8000 8001 8080 5000 5432 6379 8086

# Development command with hot reload
CMD ["python3", "-m", "cv_cnc_manufacturing.api.server", "--reload", "--host", "0.0.0.0"]

# =============================================================================
# Testing Stage - Optimized for CI/CD testing
# =============================================================================
FROM dev as testing

# Set testing environment
ENV ENVIRONMENT=testing \
    DEBUG=true \
    LOG_LEVEL=DEBUG \
    PYTEST_TIMEOUT=300

# Copy test files
COPY --chown=cvcnc:cvcnc tests/ /app/tests/

# Run tests during build (can be disabled with build arg)
ARG SKIP_TESTS=false
RUN if [ "$SKIP_TESTS" = "false" ]; then \
        python3 -m pytest tests/unit/ -v --tb=short; \
    fi

# Testing command
CMD ["python3", "-m", "pytest", "tests/", "-v", "--cov=src", "--cov-report=html"]

# =============================================================================
# Security Scanning Stage - Security validation
# =============================================================================
FROM production as security-scan

# Install security scanning tools
RUN apt-get update && apt-get install -y \
    python3-bandit \
    python3-safety \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Run security scans
RUN python3 -m bandit -r /app/src/ -f json -o /app/security-report.json || true
RUN python3 -m safety check --json --output /app/safety-report.json || true

# Security scan command
CMD ["sh", "-c", "bandit -r /app/src/ && safety check"]

# =============================================================================
# Compliance Stage - Manufacturing compliance validation
# =============================================================================
FROM production as compliance

# Copy compliance validation tools
COPY compliance/ /app/compliance/

# Set compliance environment
ENV COMPLIANCE_MODE=true \
    AUDIT_ENABLED=true

# Run compliance checks
RUN python3 -m cv_cnc_manufacturing.compliance.validate --standards ISO9001,IATF16949,IEC62443

# Compliance validation command
CMD ["python3", "-m", "cv_cnc_manufacturing.compliance.validate", "--comprehensive"]

# =============================================================================
# Manufacturing Runtime - Specialized for manufacturing environments
# =============================================================================
FROM production as manufacturing

# Install additional manufacturing tools
RUN apt-get update && apt-get install -y \
    # Industrial communication tools
    modbus-utils \
    # Network analysis tools
    tcpdump \
    nmap \
    # System monitoring
    sysstat \
    iotop \
    # Manufacturing-specific libraries
    python3-serial \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Manufacturing environment variables
ENV MANUFACTURING_MODE=true \
    INDUSTRIAL_PROTOCOLS=true \
    SAFETY_MONITORING=true \
    COMPLIANCE_LOGGING=true

# Specialized health check for manufacturing
HEALTHCHECK --interval=15s --timeout=8s --start-period=60s --retries=5 \
    CMD python3 -c "from cv_cnc_manufacturing.monitoring.health import manufacturing_health_check; manufacturing_health_check()" || exit 1

# Manufacturing-specific command
CMD ["python3", "-m", "cv_cnc_manufacturing.manufacturing.supervisor"]

# =============================================================================
# Edge Computing Stage - Optimized for edge deployment
# =============================================================================
FROM manufacturing as edge

# Remove unnecessary components for edge deployment
RUN apt-get autoremove -y && \
    python3 -m pip uninstall -y \
    sphinx sphinx-rtd-theme myst-parser \
    pytest pytest-cov pytest-mock pytest-asyncio pytest-benchmark \
    && python3 -m pip cache purge

# Edge-specific environment
ENV EDGE_MODE=true \
    RESOURCE_CONSTRAINED=true \
    OFFLINE_CAPABLE=true

# Optimized edge command
CMD ["python3", "-m", "cv_cnc_manufacturing.edge.agent"]

# =============================================================================
# Documentation Stage - Documentation generation
# =============================================================================
FROM python-deps as docs

# Install documentation dependencies
RUN python3 -m pip install sphinx sphinx-rtd-theme myst-parser

# Copy documentation source
COPY docs/ /app/docs/
COPY src/ /app/src/

WORKDIR /app

# Build documentation
RUN cd docs && make html

# Serve documentation
EXPOSE 8080
CMD ["python3", "-m", "http.server", "8080", "--directory", "docs/build/html"]

# =============================================================================
# Build Arguments and Multi-Architecture Support
# =============================================================================

# Build arguments for customization
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

# Add build metadata
LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.version=$VERSION

# Multi-architecture support
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "Building for $TARGETPLATFORM on $BUILDPLATFORM"

# =============================================================================
# Usage Examples:
# 
# Production build:
# docker build --target production -t cv-cnc-manufacturing:latest .
#
# Development build:
# docker build --target dev -t cv-cnc-manufacturing:dev .
#
# Testing build:
# docker build --target testing -t cv-cnc-manufacturing:test .
#
# Manufacturing build:
# docker build --target manufacturing -t cv-cnc-manufacturing:manufacturing .
#
# Multi-arch build:
# docker buildx build --platform linux/amd64,linux/arm64 --target production .
#
# Security scan:
# docker build --target security-scan -t cv-cnc-manufacturing:security .
#
# Documentation:
# docker build --target docs -t cv-cnc-manufacturing:docs .
# =============================================================================
