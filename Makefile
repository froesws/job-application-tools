.PHONY: install lint typecheck test-backend check-committed-data check build

install:
	uv sync

lint:
	uv run ruff check backend

typecheck:
	uv run mypy

test-backend:
	uv run pytest

check-committed-data:
	@files=$$(git ls-files -- 'profile/*/master.json' 'profile/*/blocklist.txt'); \
	if [ -n "$$files" ]; then \
		echo "refusing: real profile data is tracked (commit the .example files instead):"; \
		echo "$$files"; \
		exit 1; \
	fi; \
	echo "committed-data check ok"

check: lint typecheck test-backend check-committed-data

build:
	uv run python -m compileall -q backend/src
