# Energy Cost Analysis System - Development Commands

.PHONY: help dev-up dev-down seed-demo test lint clean api-logs worker-logs scheduler-logs api-shell test-api db-status server-status server-scale db-vacuum db-backup monitoring-up monitoring-down audit-log

help: ## Show this help message
	@echo "Energy Cost Analysis System - Available Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev-up: ## Start local development environment
	@echo "Starting Energy Cost Analysis System..."
	docker compose up --build -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services available at:"
	@echo "  - Database: localhost:5432"
	@echo "  - Redis: localhost:6379"
	@echo "  - OpenSearch: http://localhost:9200"
	@echo "  - MinIO Console: http://localhost:9001"
	@echo "  - API: http://localhost:8000"
	@echo "  - Worker: http://localhost:8001"
	@echo "  - Scheduler: http://localhost:8002"

dev-down: ## Stop local development environment
	docker compose down

dev-logs: ## Show logs from all services
	docker compose logs -f

seed-demo: ## Run demo data seeding
	@echo "Starting energy cost analysis demo pipeline..."
	@echo "Checking services..."
	@curl -f http://localhost:8000/healthz > /dev/null 2>&1 || (echo "API not ready. Run 'make dev-up' first." && exit 1)
	@echo "✓ API service ready"
	@echo "Triggering search ingest..."
	@curl -X POST http://localhost:8000/api/ingest/search \
		-H "Content-Type: application/json" \
		-d '{"query_set": ["solar panels LCOE", "battery storage LCOS", "energy cost analysis", "renewable energy economics"]}' \
		> /dev/null 2>&1
	@echo "✓ Search ingest queued"
	@echo "Triggering fact extraction..."
	@curl -X POST http://localhost:8000/api/extract > /dev/null 2>&1
	@echo "✓ Fact extraction queued"
	@echo "Computing LCOE for default scenario..."
	@curl -X POST http://localhost:8000/api/compute/lcoe \
		-H "Content-Type: application/json" \
		-d '{"scenario_id": 1}' \
		> /dev/null 2>&1
	@echo "✓ LCOE computation queued"
	@echo ""
	@echo "Demo pipeline started successfully!"
	@echo "Monitor progress with: make worker-logs"
	@echo "View results at: http://localhost:3000/dashboard"
	@echo ""

test: ## Run all tests
	@echo "Running tests..."
	@echo "Test suite will be implemented with the API"

lint: ## Run linting and formatting
	@echo "Running linters..."
	@echo "Linting will be implemented with the codebase"

clean: ## Clean up development environment
	docker compose down -v
	docker system prune -f

db-reset: ## Reset database (WARNING: destroys all data)
	docker compose down -v
	docker compose up db -d
	@sleep 5
	@echo "Database reset complete"

logs-db: ## Show database logs
	docker compose logs -f db

logs-redis: ## Show Redis logs
	docker compose logs -f redis

logs-opensearch: ## Show OpenSearch logs
	docker compose logs -f opensearch

api-logs: ## Show API service logs
	docker compose logs -f api

worker-logs: ## Show worker service logs
	docker compose logs -f worker

scheduler-logs: ## Show scheduler service logs
	docker compose logs -f scheduler

api-shell: ## Open shell in API container
	docker compose exec api bash

test-api: ## Test API endpoints
	@echo "Testing API endpoints..."
	curl -f http://localhost:8000/healthz || echo "API not ready"
	curl -f http://localhost:8000/api/entities || echo "Entities endpoint not ready"

# Added monitoring and admin commands
db-status: ## Check database health status
	@echo "Checking database status..."
	curl -s http://localhost:8000/api/admin/db/status | jq '.' || echo "Database status check failed"

server-status: ## Check server resource status
	@echo "Checking server status..."
	curl -s http://localhost:8000/api/admin/server/status | jq '.' || echo "Server status check failed"

server-scale: ## Scale worker services (usage: make server-scale workers=4)
	@echo "Scaling workers to $(workers) replicas..."
	curl -X POST http://localhost:8000/api/admin/server/control \
		-H "Content-Type: application/json" \
		-d '{"action": "scale_worker", "target": "worker", "replicas": $(workers)}' | jq '.'

db-vacuum: ## Run database vacuum analyze
	@echo "Running database vacuum analyze..."
	curl -X POST http://localhost:8000/api/admin/db/control \
		-H "Content-Type: application/json" \
		-d '{"action": "vacuum_analyze"}' | jq '.'

db-backup: ## Trigger database backup
	@echo "Triggering database backup..."
	curl -X POST http://localhost:8000/api/admin/db/control \
		-H "Content-Type: application/json" \
		-d '{"action": "backup_snapshot"}' | jq '.'

monitoring-up: ## Start monitoring stack (Prometheus, Grafana)
	@echo "Starting monitoring stack..."
	docker compose -f docker-compose.monitoring.yml up -d
	@echo "Monitoring available at:"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Grafana: http://localhost:3001 (admin/admin)"

monitoring-down: ## Stop monitoring stack
	docker compose -f docker-compose.monitoring.yml down

audit-log: ## View admin action audit log
	@echo "Recent admin actions:"
	curl -s http://localhost:8000/api/admin/audit | jq '.[] | {user: .user_email, action: .action, target: .target, time: .ts}'
