.PHONY: help build up down logs test clean restart backend-test frontend-dev

help: ## Show this help message
	@echo "OpenStack Admin Assistant Portal - Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker compose build

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

logs: ## View logs from all services
	docker compose logs -f

restart: down up ## Restart all services

test: ## Run backend tests
	cd backend && pytest app/tests/ -v

backend-test: ## Run backend tests in Docker
	docker compose exec api pytest app/tests/ -v

clean: ## Remove all containers, volumes, and images
	docker compose down -v --rmi all
	rm -rf backend/__pycache__
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

frontend-dev: ## Run frontend with simple HTTP server
	cd frontend && python3 -m http.server 3000

backend-dev: ## Run backend in development mode (local)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

health: ## Check health of all services
	@echo "Checking API health..."
	@curl -s http://localhost:8088/api/health | jq . || echo "API not responding"
	@echo ""
	@echo "Checking Nginx health..."
	@curl -s http://localhost:8088/health || echo "Nginx not responding"

ps: ## Show running containers
	docker compose ps

shell-api: ## Open shell in API container
	docker compose exec api sh

shell-nginx: ## Open shell in Nginx container
	docker compose exec nginx sh
