.PHONY: help up up-dev down logs restart build clean migrate test-backend shell-backend shell-db

# Default target
help: ## Show this help message
	@echo "Room — available commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

up: ## Start all services (production mode)
	docker-compose up -d

up-dev: ## Start all services with hot-reload (development mode)
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

down: ## Stop all services
	docker-compose down

logs: ## View logs for all services (Ctrl+C to exit)
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

restart: ## Restart all services
	docker-compose restart

build: ## Rebuild Docker images
	docker-compose build --no-cache

clean: ## Remove containers, networks, and volumes (WARNING: deletes DB data)
	docker-compose down -v --remove-orphans

migrate: ## Run Alembic database migrations
	docker-compose exec backend alembic upgrade head

migration: ## Create a new Alembic migration (usage: make migration MSG="description")
	docker-compose exec backend alembic revision --autogenerate -m "$(MSG)"

test-backend: ## Run backend tests
	docker-compose exec backend pytest -v

shell-backend: ## Open a shell inside the backend container
	docker-compose exec backend /bin/sh

shell-db: ## Open a psql shell inside the postgres container
	docker-compose exec postgres psql -U $${POSTGRES_USER:-room} -d $${POSTGRES_DB:-room}
