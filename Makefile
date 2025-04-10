all: test

test:
	@echo "Running tests..."
	uv run pytest -v -s --cov ./unfazed_celery --cov-report term-missing

format:
	@echo "Formatting code..."
	uv run ruff format tests/ unfazed_celery/
	uv run ruff check tests/ unfazed_celery/  --fix
	uv run mypy --check-untyped-defs --explicit-package-bases --ignore-missing-imports tests/ unfazed_celery/

publish:
	@echo "Publishing package..."
	uv build
	uv publish