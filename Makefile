.PHONY: setup install check test live serve
setup:
	uv sync --locked
install: setup
	uv run --locked python scripts/install_codex.py
check:
	./scripts/check.sh
test:
	uv run --locked pytest
live:
	uv run --locked python scripts/live_smoke.py
serve:
	uv run --locked canvas-mcp
