.PHONY: run test lint typecheck db-upgrade db-downgrade

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -q

lint:
	ruff check .

typecheck:
	mypy app

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1
