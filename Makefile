.PHONY: lint format typecheck validate test dev clean

lint:
	uv run ruff check src/

format:
	uv run ruff format src/

typecheck:
	uv run mypy src/ --ignore-missing-imports

validate: lint typecheck
	@echo "All checks passed"

test:
	uv run pytest tests/ -v

dev:
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

install:
	uv sync

install-dev:
	uv sync --extra dev

pre-commit-install:
	uv run pre-commit install
