check:
	ruff check

fix:
	ruff check --fix

format:
	ruff format

run:
	python3 main.py

run-django:
	cd djangoadmin; python3 manage.py runserver

collectstatic:
	cd djangoadmin; python3 manage.py collectstatic --no-input

alembic-init:
	alembic init --template async alembic

makemig:
	alembic revision --autogenerate -m "<name of migration>"

migrate:
	alembic upgrade head

makemig-compose:
	sudo docker compose -f docker-compose.local.yml exec -it app alembic revision --autogenerate -m "<name of migration>"

migrate-compose:
	sudo docker compose -f docker-compose.local.yml exec -it app alembic upgrade head

downgrade:
	alembic downgrade -1

pytest-one-test:
	pytest tests/<path to test file>.py::<class name>::<method name>

build-compose:
	sudo docker compose -f docker-compose.local.yml up --build -d --remove-orphans

stop-compose:
	sudo docker compose -f docker-compose.local.yml stop

start-compose:
	sudo docker compose -f docker-compose.local.yml start

collectstatic-compose:
	sudo docker compose -f docker-compose.local.yml exec -it djangoadmin python manage.py collectstatic --no-input

superuser-compose:
	sudo docker compose -f docker-compose.local.yml exec -it djangoadmin python manage.py createsuperuser --email admin@admin.com --username admin -v 3

ls-container:
	sudo docker container ls -a

logs-app:
	sudo docker logs --tail 50 --follow --timestamps blackjack_bot_app

logs-djangoadmin:
	sudo docker logs --tail 50 --follow --timestamps blackjack_bot_djangoadmin

logs-db:
	sudo docker logs --tail 50 --follow --timestamps blackjack_bot_db

logs-nginx:
	sudo docker logs --tail 50 --follow --timestamps blackjack_bot_nginx

logs-rabbit:
	sudo docker logs --tail 50 --follow --timestamps blackjack_bot_rabbitmq

ls-app-compose:
	sudo docker compose -f docker-compose.local.yml exec -it app ls

ls-djangoadmin-compose:
	sudo docker compose -f docker-compose.local.yml exec -it djangoadmin ls
