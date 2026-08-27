# List all recipes
[private]
@default:
    just --list --unsorted

# Run app
[group("App")]
run:
    uv run flashcard-generator

# Run app with auto-reload
[group("App")]
dev:
    FLASHCARD_GENERATOR_LOG_LEVEL="DEBUG" uv run gradio src/flashcard_generator/app.py

# Fix formatting
[group("Mutating QA")]
format:
    uv run ruff format

# Fix linting errors
[group("Mutating QA")]
lint-fix:
    uv run ruff check --fix

# Fix code: lint, format
[group("Mutating QA")]
fix: lint-fix format

# Check formatting
[group("Non-Mutating QA")]
format-check:
    uv run ruff format --check

# Check linting errors
[group("Non-Mutating QA")]
lint:
    uv run ruff check

# Check typing
[group("Non-Mutating QA")]
typecheck:
    # TODO: Remove this workaround once the upstream bug fixed:
    # github.com/gradio-app/gradio/issues/13781
    uv run python -c "import gradio"
    uv run mypy .

# Run tests
[group("Non-Mutating QA")]
test:
    uv run pytest

# Check code: format, lint, type, test
[group("Non-Mutating QA")]
check: format-check lint typecheck test
