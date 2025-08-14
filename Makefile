PROJECT_NAME = todo-py
DOCKER_COMPOSE = docker compose -p $(PROJECT_NAME) -f docker/docker-compose.yml

dev:
	docker compose -f docker/docker-compose.yml up --build

# Service control
up:
	${DOCKER_COMPOSE} up -d

down:
	${DOCKER_COMPOSE} down

down-v:
	${DOCKER_COMPOSE} down -v

restart:
	${DOCKER_COMPOSE} down && ${DOCKER_COMPOSE} up -d

logs:
	${DOCKER_COMPOSE} logs -f

# Rebuild all services
build:
	${DOCKER_COMPOSE} build --progress=plain