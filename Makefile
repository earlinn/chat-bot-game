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
