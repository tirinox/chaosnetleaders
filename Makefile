include .env
export

buildf:
	$(info Make: Building frontend.)
	cd frontend && yarn install && yarn run build
	docker-compose -f "${DOCKER_COMPOSE_FILE}" restart nginx

buildb:
	$(info Make: Building images.)
	docker-compose -f "${DOCKER_COMPOSE_FILE}" build --no-cache backend

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
	@make -s start

dbcli:
	@docker-compose -f "${DOCKER_COMPOSE_FILE}" exec db psql "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}"

certbot:
	sudo certbot certonly --webroot -w ./frontend/dist/ -d ${DOMAIN}
