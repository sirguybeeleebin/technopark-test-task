.PHONY: format lint test prune up

format:
	poetry run autoflake --in-place --remove-unused-variables --remove-all-unused-imports -r .
	poetry run isort .
	poetry run ruff format .

lint:
	poetry run ruff check .

test:
	poetry run pytest -v --log-cli-level=INFO

prune:
	docker container prune -f
	docker volume prune -f
	docker volume rm technopark-test-task_postgres_data

up:
	docker compose --env-file .env up --build
