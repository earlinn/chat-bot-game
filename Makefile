check:
	ruff check

fix:
	ruff check --fix

format:
	ruff format

alembic-init:
	alembic init --template async alembic

makemig:
	alembic revision --autogenerate -m "<name of migration>"

migrate:
	alembic upgrade head

downgrade:
	alembic downgrade -1

pytest-one-test:
	pytest tests/<path to test file>.py::<class name>::<method name>

build-compose:
	sudo docker compose up --build -d --remove-orphans

stop-compose:
	sudo docker compose stop

start-compose:
	sudo docker compose start

logs-app:
	sudo docker logs --tail 50 --follow --timestamps blackjack_bot_app

logs-db:
	sudo docker logs --tail 50 --follow --timestamps blackjack_bot_db

logs-nginx:
	sudo docker logs --tail 50 --follow --timestamps blackjack_bot_nginx

ls-app-compose:
	sudo docker compose exec -it app ls
