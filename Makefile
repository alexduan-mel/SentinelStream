.PHONY: up down logs ps db-shell redis-shell

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

db-shell:
	docker compose exec timescaledb psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-sentinel}

redis-shell:
	docker compose exec redis redis-cli
