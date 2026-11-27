# Atajos de desarrollo. El compose lo provee el entorno Base44:
#   make COMPOSE="docker compose -f /ruta/docker-compose.base44.yml" up
COMPOSE ?= docker compose -f docker-compose.base44.yml

.PHONY: up down ps logs migrate test test-web load update admin

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) run --rm migrate

test:
	$(COMPOSE) exec -T api python -m pytest -q

test-web:
	$(COMPOSE) exec -T web node node_modules/vitest/vitest.mjs run

load:
	$(COMPOSE) exec -T api python -m scripts.load_sources bacn --limite 5

update:
	$(COMPOSE) exec -T worker python -m app.jobs.scheduler --once

admin:
	$(COMPOSE) exec -T api python -m scripts.promote_admin --email $(EMAIL)
