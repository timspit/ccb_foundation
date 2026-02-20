.PHONY: help build up down logs shell test clean

help: ## Show this help message
	@echo "Massachusetts Recovery Services Directory - Docker Commands"
	@echo "========================================================"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build the Docker image
	docker-compose build

up: ## Start the application
	docker-compose up -d

down: ## Stop the application
	docker-compose down

logs: ## View application logs
	docker-compose logs -f app

shell: ## Open a shell in the running container
	docker-compose exec app bash

test: ## Run tests in the container
	docker-compose exec app python -m pytest

test-cov: ## Run tests with coverage
	docker-compose exec app python -m pytest --cov=. --cov-report=html

clean: ## Clean up Docker resources
	docker-compose down -v --remove-orphans
	docker system prune -f

dev: ## Start development environment
	docker-compose -f docker-compose.dev.yml up -d

dev-down: ## Stop development environment
	docker-compose -f docker-compose.dev.yml down

dev-logs: ## View development logs
	docker-compose -f docker-compose.dev.yml logs -f app

dev-shell: ## Open shell in development container
	docker-compose -f docker-compose.dev.yml exec app bash

install: ## Install dependencies in container
	docker-compose exec app pip install -r requirements.txt

update: ## Update dependencies
	docker-compose exec app pip install --upgrade -r requirements.txt

format: ## Format code with black
	docker-compose exec app black .

lint: ## Run flake8 linting
	docker-compose exec app flake8 .

health: ## Check application health
	curl -f http://localhost:5000/health || echo "Application not responding"

