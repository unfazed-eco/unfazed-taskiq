all: test

test:
	@echo "Running tests..."
	uv run pytest -v -s --cov ./unfazed_taskiq --cov-report term-missing

format:
	@echo "Formatting code..."
	uv run ruff format tests/ unfazed_taskiq/
	uv run ruff check tests/ unfazed_taskiq/  --fix
	uv run mypy --check-untyped-defs --explicit-package-bases --ignore-missing-imports tests/ unfazed_taskiq/

publish:
	@echo "Publishing package..."
	uv build
	uv publish
