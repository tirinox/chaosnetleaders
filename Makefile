include .env
export

build:
	$(info Make: Building images.)
	docker-compose -f "${DOCKER_COMPOSE_FILE}" build --no-cache backend nginx

start:
	$(info Make: Starting containers.)
	docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d
	docker ps

stop:
	$(info Make: Stopping containers.)
	@docker-compose -f "${DOCKER_COMPOSE_FILE}" stop

restart:
	$(info Make: Restarting containers.)
	@make -s stop
	@make -s start

pull:
	git pull

logs:
	@docker-compose -f "${DOCKER_COMPOSE_FILE}" logs --follow --tail 1000 --timestamps

clean:
	@docker system prune --volumes --force

upgrade:
	@make -s pull
	@make -s build
	@make -s start
