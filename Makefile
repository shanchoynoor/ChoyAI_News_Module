.PHONY: install run test clean deploy

# Default target
all: install

# Install dependencies
install:
	pip install -r config/requirements.txt
	pip install -e .

# Run the application
run:
	./bin/choynews

# Run the bot only
bot:
	./bin/choynews --service bot

# Run the auto news service only
auto:
	./bin/choynews --service auto

# Run tests
test:
	python -m pytest tests/

# Clean up generated files
clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".pytest_cache" -type d -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "*.egg-info" -type d -exec rm -rf {} +
	find . -name "*.egg" -delete
	find . -name "*.log" -delete

# Deploy the application
deploy:
	./tools/deploy/setup_server.sh
