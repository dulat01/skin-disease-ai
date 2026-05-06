.PHONY: help build up down logs shell migrate seed test clean

# Default target
help:
	@echo "Skin Disease AI Backend - Available Commands"
	@echo "============================================"
	@echo ""
	@echo "Development:"
	@echo "  make build          - Build all Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View all logs"
	@echo "  make logs-f         - Follow all logs"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        - Run all database migrations"
	@echo "  make migrate-auth   - Run auth service migrations"
	@echo "  make migrate-pred   - Run prediction service migrations"
	@echo "  make migrate-admin  - Run admin service migrations"
	@echo "  make seed           - Seed database with test data"
	@echo ""
	@echo "Services:"
	@echo "  make shell-api      - Shell into API gateway container"
	@echo "  make shell-auth     - Shell into auth service container"
	@echo "  make shell-pred     - Shell into prediction service container"
	@echo "  make shell-admin    - Shell into admin service container"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-auth      - Run auth service tests"
	@echo "  make test-pred      - Run prediction service tests"
	@echo "  make test-admin     - Run admin service tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          - Remove all containers and volumes"
	@echo "  make ps             - List running containers"
	@echo "  make health         - Check service health"

# =============================================================================
# DEVELOPMENT
# =============================================================================

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart: down up

logs:
	docker-compose logs

logs-f:
	docker-compose logs -f

ps:
	docker-compose ps

# =============================================================================
# DATABASE MIGRATIONS
# =============================================================================

migrate: migrate-auth migrate-pred migrate-admin

migrate-auth:
	docker-compose exec auth-service alembic upgrade head

migrate-pred:
	docker-compose exec prediction-service alembic upgrade head

migrate-admin:
	docker-compose exec admin-service alembic upgrade head

seed:
	docker-compose exec auth-service python -m app.scripts.seed_data

# =============================================================================
# SHELL ACCESS
# =============================================================================

shell-api:
	docker-compose exec api-gateway /bin/sh

shell-auth:
	docker-compose exec auth-service /bin/sh

shell-pred:
	docker-compose exec prediction-service /bin/sh

shell-admin:
	docker-compose exec admin-service /bin/sh

shell-db:
	docker-compose exec postgres psql -U postgres

shell-redis:
	docker-compose exec redis redis-cli -a redis123

# =============================================================================
# TESTING
# =============================================================================

test:
	docker-compose exec api-gateway pytest
	docker-compose exec auth-service pytest
	docker-compose exec prediction-service pytest
	docker-compose exec admin-service pytest

test-auth:
	docker-compose exec auth-service pytest -v

test-pred:
	docker-compose exec prediction-service pytest -v

test-admin:
	docker-compose exec admin-service pytest -v

# =============================================================================
# HEALTH CHECKS
# =============================================================================

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "API Gateway: DOWN"
	@curl -s http://localhost:8001/health | jq . || echo "Auth Service: DOWN"
	@curl -s http://localhost:8002/health | jq . || echo "Prediction Service: DOWN"
	@curl -s http://localhost:8003/health | jq . || echo "Admin Service: DOWN"

# =============================================================================
# CLEANUP
# =============================================================================

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

clean-all: clean
	docker volume rm $$(docker volume ls -q -f name=skin-disease) 2>/dev/null || true
