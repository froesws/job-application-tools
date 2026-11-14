.PHONY: install lint test-backend check-committed-data check build

install:
	uv sync

lint:
	uv run ruff check backend

test-backend:
	@if uv run python -c "import pytest" >/dev/null 2>&1; then \
		uv run pytest backend -q; \
	else \
		echo "pytest not installed yet — backend tests not yet authored; skipping"; \
	fi

check-committed-data:
	@test ! -f profile/master.json || \
		(echo "refusing: commit profile/master.example.json, not profile/master.json" && false)
	@echo "committed-data check ok"

check: lint test-backend check-committed-data

build:
	uv run python -m compileall -q backend/src
