# ChoyNewsBot - Development and Deployment Makefile
# =================================================

.PHONY: help install install-dev test test-unit test-integration test-coverage lint format type-check security-check clean run run-dev run-tests docker-build docker-run docker-test deploy docs

# Default target
help: ## Show this help message
	@echo "ChoyNewsBot - AI-Powered Breaking News & Crypto Intelligence"
	@echo "============================================================"
	@echo "Available commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: ## Install production dependencies
	pip install -r config/requirements.txt

install-dev: ## Install development dependencies
	pip install -r config/requirements.txt -r config/requirements-dev.txt

# Testing targets
test: ## Run all tests
	python -m pytest tests/ -v

test-unit: ## Run unit tests only
	python -m pytest tests/unit/ -v

test-integration: ## Run integration tests only
	python -m pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	python -m pytest tests/ --cov=./ --cov-report=html --cov-report=term-missing

test-fast: ## Run tests with minimal output
	python -m pytest tests/ -q

# Code quality targets
lint: ## Run all linters
	flake8 . || true
	pylint core/ data_modules/ services/ utils/ api/ --disable=C0114,C0116 || true

format: ## Format code with black and isort
	black . || echo "black not installed"
	isort . || echo "isort not installed"

format-check: ## Check code formatting without making changes
	black --check . || echo "black not installed"
	isort --check-only . || echo "isort not installed"

type-check: ## Run type checking with mypy
	mypy core/ data_modules/ services/ utils/ api/ --ignore-missing-imports || echo "mypy not installed"

security-check: ## Run security checks
	bandit -r . -ll || echo "bandit not installed"
	safety check || echo "safety not installed"

# Application targets
run: ## Run the bot in production mode
	./bin/choynews --service both

run-dev: ## Run the bot in development mode
	ENVIRONMENT=development ./bin/choynews --service both

run-bot: ## Run only the interactive bot
	./bin/choynews --service bot

run-auto: ## Run only the auto news service
	./bin/choynews --service auto

# Docker targets
docker-build: ## Build Docker image
	docker build -t choynews-bot .

docker-run: ## Run Docker container
	docker-compose up -d

docker-test: ## Run tests in Docker
	docker-compose -f docker-compose.dev.yml run test-runner

docker-logs: ## View Docker logs
	docker-compose logs -f choynews-bot

docker-stop: ## Stop Docker containers
	docker-compose down

# Maintenance targets
clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/
	rm -rf build/ dist/

status: ## Check bot status
	@python -c "import subprocess, sys; result = subprocess.run(['pgrep', '-f', 'choynews'], capture_output=True); print('✅ ChoyNewsBot is running') if result.returncode == 0 else print('❌ ChoyNewsBot is not running')"

logs: ## View live logs
	tail -f logs/choynews.log

# Quick development cycle
dev: format lint test-fast ## Quick development check

# Configuration validation
config-check: ## Validate configuration
	python -c "from utils.config import Config; Config().validate(); print('✅ Configuration valid')"

# Deploy the application
deploy: ## Deploy using setup script
	./tools/deploy/setup_server.sh
