# ChoyNewsBot - AI-Powered Breaking News & Crypto Intelligence
# =============================================================

.PHONY: help install install-dev test lint format run clean docker-build logs status config-check
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "ChoyNewsBot - AI-Powered Breaking News & Crypto Intelligence"
	@echo "============================================================"
	@echo "Available commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "%-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	@echo "📦 Installing production dependencies..."
	pip install --upgrade pip
	pip install -r config/requirements.txt

install-dev: ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	pip install --upgrade pip
	pip install -r config/requirements.txt
	pip install -r config/requirements-dev.txt
	pip install -e .

test: ## Run all tests
	@echo "🧪 Running tests..."
	python -m pytest tests/ -v

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	python -m pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	python -m pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	python -m pytest tests/ --cov=choynews --cov-report=html

test-fast: ## Run tests with minimal output
	@echo "🧪 Running fast tests..."
	python -m pytest tests/ -q

lint: ## Run all linters
	@echo "🔍 Running linters..."
	python -m flake8 core/ utils/ services/ data_modules/ api/ || true
	python -m pylint core/ utils/ services/ data_modules/ api/ || true

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	python -m black core/ utils/ services/ data_modules/ api/ tests/ || true
	python -m isort core/ utils/ services/ data_modules/ api/ tests/ || true

format-check: ## Check code formatting without making changes
	@echo "🎨 Checking code format..."
	python -m black --check core/ utils/ services/ data_modules/ api/ || true
	python -m isort --check-only core/ utils/ services/ data_modules/ api/ || true

type-check: ## Run type checking with mypy
	@echo "📝 Running type checks..."
	python -m mypy core/ utils/ services/ data_modules/ api/ || true

security-check: ## Run security checks
	@echo "🔒 Running security checks..."
	python -m bandit -r core/ utils/ services/ data_modules/ api/ || true
	python -m safety check || true

run: ## Run the bot in production mode
	@echo "🚀 Starting bot in production mode..."
	./bin/choynews --service both

run-dev: ## Run the bot in development mode
	@echo "🚀 Starting bot in development mode..."
	./bin/choynews --service both --debug

run-bot: ## Run only the interactive bot
	@echo "🚀 Starting interactive bot only..."
	./bin/choynews --service bot

run-auto: ## Run only the auto news service
	@echo "🚀 Starting auto news service only..."
	./bin/choynews --service auto

start: ## Start the bot in production mode
	@echo "🚀 Starting ChoyNewsBot..."
	./bin/choynews --service both

stop: ## Stop the bot service
	@echo "🛑 Stopping ChoyNewsBot..."
	@pkill -f "choynews" || echo "No running instances found"

restart: ## Restart the bot service
	@echo "🔄 Restarting ChoyNewsBot..."
	@$(MAKE) stop
	@sleep 2
	@$(MAKE) start

daemon: ## Start bot as background daemon
	@echo "🌙 Starting ChoyNewsBot as daemon..."
	nohup ./bin/choynews --service both > logs/daemon.log 2>&1 &
	@echo "Bot started in background. Check logs with: make logs"

docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t choynews-bot .

docker-run: ## Run Docker container
	@echo "🐳 Running Docker container..."
	@mkdir -p $(PWD)/data $(PWD)/logs
	@chmod 777 $(PWD)/data $(PWD)/logs
	docker run -d --name choynews-bot --user root --env-file .env -v $(PWD)/data:/app/data -v $(PWD)/logs:/app/logs choynews-bot

docker-test: ## Run tests in Docker
	@echo "🐳 Running tests in Docker..."
	docker run --rm choynews-bot python -m pytest tests/

docker-logs: ## View Docker logs
	@echo "🐳 Viewing Docker logs..."
	docker logs -f choynews-bot

docker-stop: ## Stop Docker containers
	@echo "🐳 Stopping Docker containers..."
	docker stop choynews-bot || true
	docker rm choynews-bot || true

clean: ## Clean up temporary files
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ htmlcov/ .coverage

status: ## Check bot status
	@echo "📊 Checking bot status..."
	@ps aux | grep choynews || echo "Bot not running"
	@echo "Recent log entries:"
	@tail -5 logs/choynews.log 2>/dev/null || echo "No logs found"

logs: ## View live logs
	@echo "📝 Viewing live logs..."
	@tail -f logs/choynews.log

dev: ## Quick development check
	@echo "🔧 Running development checks..."
	@$(MAKE) format-check
	@$(MAKE) test-fast
	@echo "✅ Development checks complete"

config-check: ## Validate configuration
	@echo "⚙️ Validating configuration..."
	@python3 -c "import sys; sys.path.insert(0, '.'); from utils.config import Config; Config().validate(); print('✅ Configuration valid')"

deploy: ## Deploy using setup script
	@echo "🚀 Deploying..."
	@if [ -f tools/deploy/setup_server_fix.sh ]; then chmod +x tools/deploy/setup_server_fix.sh; ./tools/deploy/setup_server_fix.sh; else echo "Deploy script not found"; fi
