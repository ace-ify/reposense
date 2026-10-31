.PHONY: install test lint run infra-up infra-down
install:
	python -m pip install -e ".[dev]"
test:
	pytest -q
lint:
	ruff check .
run:
	uvicorn backend.app.main:app --reload
infra-up:
	docker compose up -d
infra-down:
	docker compose down
