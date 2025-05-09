# Directories for source code and tests
SOURCE_DIR := "aibolit_app"
TESTS_DIR := "tests"

# Default command: list available commands
default:
    @just --list

# Environment variables file
set dotenv-filename := ".env"

# Run all checks: linters and formatting validation
lint: ruff-check ruff format

# --- Dependency Management ---

# Update project dependencies
[group('dependencies')]
update:
    uv sync --upgrade

# --- Linters and Formatting ---

# Automatically format code
[group('linters')]
format:
    uv run ruff format .


# Lint code using Ruff
[group('linters')]
ruff-check:
    uv run ruff check {{ SOURCE_DIR }}
    uv run ruff check {{ TESTS_DIR }}

# Fix code using Ruff
[group('linters')]
ruff:
    uv run ruff check --fix {{ SOURCE_DIR }}
    uv run ruff check --fix {{ TESTS_DIR }}


# --- Testing ---

# Run tests using pytest
[group('testing')]
tests:
    pytest . --cov=.

# --- Code generation ---

[group('code-generation')]
openapi-codegen:
    datamodel-codegen --input openapi.json --openapi-scopes schemas --input-file-type openapi --output {{SOURCE_DIR}}/api/schemas/schedules/generated.py

[group('code-generation')]
[working-directory: 'aibolit_app/grpc/generated']
grpc-codegen:
    python -m grpc_tools.protoc -I ../../../protos/ --python_out=. --pyi_out=. --grpc_python_out=. ../../../protos/schedule.proto
