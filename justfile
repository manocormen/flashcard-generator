default:
    @just --list

run:
    uv run flashcard-generator

format:
    uv run ruff format

lint-fix:
    uv run ruff check --fix

fix: lint-fix format

format-check:
    uv run ruff format --check

lint:
    uv run ruff check

typecheck:
    uv run mypy .

test:
    uv run pytest

check: format-check lint typecheck test
