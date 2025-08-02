# Computer Vision CNC Manufacturing Platform - Makefile
# Comprehensive development, testing, and deployment automation

.PHONY: help install install-dev test test-unit test-integration test-performance \
        test-security test-compliance lint format type-check security-scan \
        clean build docker-build docker-run docker-compose-up docker-compose-down \
        docs docs-serve deploy-dev deploy-staging deploy-prod backup restore \
        manufacturing-setup cnc-connect quality-check maintenance-check \
        compliance-validate export-control-check certificates-generate

# Default Python interpreter
PYTHON := python
PIP := pip
PYTEST := pytest
BLACK := black
ISORT := isort
MYPY := mypy
FLAKE8 := flake8
BANDIT := bandit
SAFETY := safety

# Project directories
SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs
CONFIG_DIR := configs
CERT_DIR := certs
LOG_DIR := logs
DATA_DIR := data

# Docker and deployment
DOCKER_IMAGE := cv-cnc-manufacturing
DOCKER_TAG := latest
COMPOSE_FILE := docker-compose.yml

# Manufacturing configuration
CNC_CONFIG := $(CONFIG_DIR)/cnc_machines.yaml
QUALITY_CONFIG := $(CONFIG_DIR)/quality_control.yaml
MAINTENANCE_CONFIG := $(CONFIG_DIR)/predictive_maintenance.yaml

##@ Help

help: ## Display this help message
	@echo "Computer Vision CNC Manufacturing Platform - Development Commands"
	@echo "=================================================================="
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development Setup

install: ## Install production dependencies
	@echo "🔧 Installing production dependencies..."
	$(PIP) install -e .
	@echo "✅ Production dependencies installed"

install-dev: ## Install development dependencies
	@echo "🔧 Installing development dependencies..."
	$(PIP) install -e .[dev,test,docs,security]
	pre-commit install
	@echo "✅ Development environment ready"

setup: ## Complete project setup
	@echo "🚀 Setting up Computer Vision CNC Manufacturing Platform..."
	$(PYTHON) setup.py --dev
	@echo "✅ Project setup completed"

clean: ## Clean build artifacts and temporary files
	@echo "🧹 Cleaning build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/
	rm -rf $(LOG_DIR)/*.log
	@echo "✅ Cleanup completed"

##@ Testing

test: ## Run all tests
	@echo "🧪 Running comprehensive test suite..."
	$(PYTEST) $(TEST_DIR)/ -v --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@echo "✅ All tests completed"

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	$(PYTEST) $(TEST_DIR)/unit/ -v -m "unit"
	@echo "✅ Unit tests completed"

test-integration: ## Run integration tests
	@echo "🧪 Running integration tests..."
	$(PYTEST) $(TEST_DIR)/integration/ -v -m "integration"
	@echo "✅ Integration tests completed"

test-performance: ## Run performance tests
	@echo "🧪 Running performance tests..."
	$(PYTEST) $(TEST_DIR)/performance/ -v -m "performance" --benchmark-only
	@echo "✅ Performance tests completed"

test-security: ## Run security tests
	@echo "🔒 Running security tests..."
	$(PYTEST) $(TEST_DIR)/security/ -v -m "security"
	@echo "✅ Security tests completed"

test-compliance: ## Run compliance validation tests
	@echo "📋 Running compliance tests..."
	$(PYTEST) $(TEST_DIR)/compliance/ -v -m "compliance"
	@echo "✅ Compliance tests completed"

test-manufacturing: ## Run manufacturing-specific tests
	@echo "🏭 Running manufacturing tests..."
	$(PYTEST) $(TEST_DIR)/ -v -m "manufacturing or cnc_integration"
	@echo "✅ Manufacturing tests completed"

##@ Code Quality

lint: ## Run all linting checks
	@echo "🔍 Running linting checks..."
	$(FLAKE8) $(SRC_DIR) $(TEST_DIR)
	$(BLACK) --check $(SRC_DIR) $(TEST_DIR)
	$(ISORT) --check-only $(SRC_DIR) $(TEST_DIR)
	@echo "✅ Linting checks completed"

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	$(BLACK) $(SRC_DIR) $(TEST_DIR)
	$(ISORT) $(SRC_DIR) $(TEST_DIR)
	@echo "✅ Code formatting completed"

type-check: ## Run type checking with mypy
	@echo "🔍 Running type checking..."
	$(MYPY) $(SRC_DIR)
	@echo "✅ Type checking completed"

security-scan: ## Run security vulnerability scanning
	@echo "🔒 Running security scans..."
	$(BANDIT) -r $(SRC_DIR)/ -f json -o security-report.json
	$(SAFETY) check --json --output safety-report.json
	@echo "✅ Security scanning completed"

pre-commit: ## Run pre-commit hooks on all files
	@echo "🔧 Running pre-commit hooks..."
	pre-commit run --all-files
	@echo "✅ Pre-commit checks completed"

##@ Documentation

docs: ## Build documentation
	@echo "📚 Building documentation..."
	cd $(DOCS_DIR) && make html
	@echo "✅ Documentation built"

docs-serve: ## Serve documentation locally
	@echo "📚 Serving documentation at http://localhost:8080..."
	cd $(DOCS_DIR)/build/html && $(PYTHON) -m http.server 8080

docs-clean: ## Clean documentation build
	@echo "🧹 Cleaning documentation..."
	cd $(DOCS_DIR) && make clean
	@echo "✅ Documentation cleaned"

##@ Manufacturing Operations

manufacturing-setup: ## Initialize manufacturing environment
	@echo "🏭 Setting up manufacturing environment..."
	mkdir -p $(CONFIG_DIR) $(CERT_DIR) $(LOG_DIR) $(DATA_DIR)
	$(PYTHON) -m cv_cnc_manufacturing.setup --manufacturing
	@echo "✅ Manufacturing environment ready"

cnc-connect: ## Test CNC machine connections
	@echo "🔧 Testing CNC machine connections..."
	$(PYTHON) -m cv_cnc_manufacturing.cnc.test_connections --config $(CNC_CONFIG)
	@echo "✅ CNC connections verified"

quality-check: ## Run quality control validation
	@echo "🎯 Running quality control validation..."
	$(PYTHON) -m cv_cnc_manufacturing.quality.validate --config $(QUALITY_CONFIG)
	@echo "✅ Quality control validated"

maintenance-check: ## Run predictive maintenance analysis
	@echo "🔧 Running predictive maintenance analysis..."
	$(PYTHON) -m cv_cnc_manufacturing.maintenance.analyze --config $(MAINTENANCE_CONFIG)
	@echo "✅ Maintenance analysis completed"

computer-vision-test: ## Test computer vision models
	@echo "👁️ Testing computer vision models..."
	$(PYTHON) -m cv_cnc_manufacturing.vision.test_models --validate-accuracy
	@echo "✅ Computer vision models validated"

##@ Security and Compliance

compliance-validate: ## Validate manufacturing compliance
	@echo "📋 Validating manufacturing compliance..."
	$(PYTHON) -m cv_cnc_manufacturing.compliance.validate --standards ISO9001,IATF16949,IEC62443
	@echo "✅ Compliance validation completed"

export-control-check: ## Check export control compliance
	@echo "🌍 Checking export control compliance..."
	$(PYTHON) -m cv_cnc_manufacturing.compliance.export_control --validate
	@echo "✅ Export control compliance verified"

certificates-generate: ## Generate security certificates
	@echo "🔐 Generating security certificates..."
	mkdir -p $(CERT_DIR)
	$(PYTHON) -m cv_cnc_manufacturing.security.generate_certificates --output $(CERT_DIR)
	@echo "✅ Security certificates generated"

security-audit: ## Perform comprehensive security audit
	@echo "🔒 Performing security audit..."
	$(PYTHON) -m cv_cnc_manufacturing.security.audit --comprehensive
	@echo "✅ Security audit completed"

##@ Docker and Containerization

docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "✅ Docker image built"

docker-run: ## Run application in Docker container
	@echo "🐳 Running Docker container..."
	docker run -p 8000:8000 --env-file .env $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-compose-up: ## Start all services with docker-compose
	@echo "🐳 Starting services with docker-compose..."
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "✅ Services started"

docker-compose-down: ## Stop all services
	@echo "🐳 Stopping services..."
	docker-compose -f $(COMPOSE_FILE) down
	@echo "✅ Services stopped"

docker-compose-logs: ## View docker-compose logs
	@echo "📋 Viewing service logs..."
	docker-compose -f $(COMPOSE_FILE) logs -f

##@ Database Operations

db-migrate: ## Run database migrations
	@echo "🗄️ Running database migrations..."
	$(PYTHON) -m cv_cnc_manufacturing.db.migrate --upgrade
	@echo "✅ Database migrations completed"

db-seed: ## Seed database with sample data
	@echo "🗄️ Seeding database..."
	$(PYTHON) -m cv_cnc_manufacturing.db.seed --manufacturing-data
	@echo "✅ Database seeded"

db-backup: ## Backup database
	@echo "💾 Creating database backup..."
	$(PYTHON) -m cv_cnc_manufacturing.db.backup --output backups/
	@echo "✅ Database backup created"

db-restore: ## Restore database from backup
	@echo "🔄 Restoring database..."
	$(PYTHON) -m cv_cnc_manufacturing.db.restore --backup $(BACKUP_FILE)
	@echo "✅ Database restored"

##@ Deployment

deploy-dev: ## Deploy to development environment
	@echo "🚀 Deploying to development..."
	$(PYTHON) -m cv_cnc_manufacturing.deploy --environment dev
	@echo "✅ Development deployment completed"

deploy-staging: ## Deploy to staging environment
	@echo "🚀 Deploying to staging..."
	$(PYTHON) -m cv_cnc_manufacturing.deploy --environment staging
	@echo "✅ Staging deployment completed"

deploy-prod: ## Deploy to production environment
	@echo "🚀 Deploying to production..."
	$(PYTHON) -m cv_cnc_manufacturing.deploy --environment production --confirm
	@echo "✅ Production deployment completed"

deploy-rollback: ## Rollback deployment
	@echo "🔄 Rolling back deployment..."
	$(PYTHON) -m cv_cnc_manufacturing.deploy --rollback
	@echo "✅ Deployment rolled back"

##@ Monitoring and Maintenance

logs-view: ## View application logs
	@echo "📋 Viewing application logs..."
	tail -f $(LOG_DIR)/cv_cnc_manufacturing.log

logs-analyze: ## Analyze logs for issues
	@echo "📊 Analyzing logs..."
	$(PYTHON) -m cv_cnc_manufacturing.monitoring.log_analyzer --recent 24h
	@echo "✅ Log analysis completed"

metrics-collect: ## Collect performance metrics
	@echo "📊 Collecting performance metrics..."
	$(PYTHON) -m cv_cnc_manufacturing.monitoring.metrics --collect --duration 1h
	@echo "✅ Metrics collected"

health-check: ## Perform system health check
	@echo "🏥 Performing health check..."
	$(PYTHON) -m cv_cnc_manufacturing.monitoring.health_check --comprehensive
	@echo "✅ Health check completed"

##@ Performance Testing

benchmark: ## Run performance benchmarks
	@echo "⚡ Running performance benchmarks..."
	$(PYTEST) $(TEST_DIR)/performance/ --benchmark-only --benchmark-sort=mean
	@echo "✅ Benchmarks completed"

load-test: ## Run load testing
	@echo "⚡ Running load tests..."
	$(PYTHON) -m cv_cnc_manufacturing.testing.load_test --duration 300 --concurrent 100
	@echo "✅ Load testing completed"

stress-test: ## Run stress testing
	@echo "⚡ Running stress tests..."
	$(PYTHON) -m cv_cnc_manufacturing.testing.stress_test --max-load
	@echo "✅ Stress testing completed"

##@ Utilities

version: ## Show version information
	@echo "📋 Version Information:"
	@$(PYTHON) -c "import cv_cnc_manufacturing; print(f'Platform Version: {cv_cnc_manufacturing.__version__}')"
	@$(PYTHON) --version
	@docker --version 2>/dev/null || echo "Docker not installed"

system-info: ## Display system information
	@echo "💻 System Information:"
	@echo "Platform: $$(uname -s)"
	@echo "Architecture: $$(uname -m)"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "CPU Cores: $$($(PYTHON) -c 'import os; print(os.cpu_count())')"
	@echo "Memory: $$($(PYTHON) -c 'import psutil; print(f\"{psutil.virtual_memory().total // (1024**3)} GB\")')" 2>/dev/null || echo "Memory info unavailable"

dependencies-check: ## Check dependency versions
	@echo "📦 Checking dependencies..."
	$(PIP) list --outdated
	@echo "✅ Dependency check completed"

update-dependencies: ## Update dependencies
	@echo "📦 Updating dependencies..."
	$(PIP) install --upgrade -e .[dev,test,docs,security]
	@echo "✅ Dependencies updated"

##@ Special Manufacturing Commands

factory-reset: ## Reset factory configuration
	@echo "🏭 Resetting factory configuration..."
	$(PYTHON) -m cv_cnc_manufacturing.factory.reset --confirm
	@echo "✅ Factory reset completed"

calibration: ## Run system calibration
	@echo "🎯 Running system calibration..."
	$(PYTHON) -m cv_cnc_manufacturing.calibration.run --cameras --sensors --cnc
	@echo "✅ Calibration completed"

production-start: ## Start production monitoring
	@echo "🏭 Starting production monitoring..."
	$(PYTHON) -m cv_cnc_manufacturing.production.start --monitor --quality-control
	@echo "✅ Production monitoring started"

production-stop: ## Stop production monitoring
	@echo "🏭 Stopping production monitoring..."
	$(PYTHON) -m cv_cnc_manufacturing.production.stop --graceful
	@echo "✅ Production monitoring stopped"

emergency-stop: ## Emergency production stop
	@echo "🚨 EMERGENCY STOP - Shutting down all systems..."
	$(PYTHON) -m cv_cnc_manufacturing.emergency.stop --all-systems
	@echo "🚨 Emergency stop completed"

##@ Development Workflow

dev-start: install-dev docker-compose-up ## Start complete development environment
	@echo "🚀 Development environment started"

dev-stop: docker-compose-down ## Stop development environment
	@echo "🛑 Development environment stopped"

dev-reset: clean dev-stop dev-start ## Reset development environment
	@echo "🔄 Development environment reset"

ci-test: lint type-check test security-scan ## Run CI test suite
	@echo "✅ CI test suite completed"

release-check: ci-test compliance-validate ## Pre-release validation
	@echo "✅ Release validation completed"

##@ Notes

# Manufacturing Safety Notes:
# - Always run 'emergency-stop' if any safety issues arise
# - Validate compliance before production deployment
# - Monitor system health continuously during operation
# - Keep security certificates up to date
# - Regularly backup manufacturing data and configurations

# Development Notes:
# - Run 'make install-dev' for complete development setup
# - Use 'make ci-test' before committing changes
# - Run 'make manufacturing-setup' for manufacturing environment
# - Use 'make help' to see all available commands
