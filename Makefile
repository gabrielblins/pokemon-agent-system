.PHONY: setup install run test lint docker build-docker run-docker stop-docker clean
# load .env file
ifneq (,$(wildcard .env))
	include .env
	export $(shell sed 's/=.*//' .env)
endif

# Setup environment
setup:
	pip install --upgrade pip
	pip install -r requirements.txt

setup-uv:
	uv pip install --upgrade pip
	uv pip install -r requirements.txt

# Install dependencies
install:
	pip install -r requirements.txt

install-uv:
	uv pip install -r requirements.txt

# Run application
run:
	uvicorn app.main:app --reload --port $(PORT)
# Run tests
test:
	pytest

# Run linting
lint:
	flake8 app tests

# Build Docker image
build-docker:
	docker build -t pokemon-multi-agent .

# Run Docker container
run-docker:
	docker compose up -d

# Stop Docker container
stop-docker:
	docker compose down

# Clean up
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".tox" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
