.PHONY: test test-unit test-integration ablate dev lint help

help:
	@echo "Available commands:"
	@echo "  make test             - Run all unit and integration tests (pytest)"
	@echo "  make test-unit        - Run unit test suite"
	@echo "  make test-integration - Run integration test suite"
	@echo "  make ablate           - Run the empirical ablation study (offline/simulation)"
	@echo "  make dev              - Start the FastAPI backend with live reload"
	@echo "  make lint             - Run basic static analysis"

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

ablate:
	python eval/run_ablation.py --ideas 5 --offline

dev:
	uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

lint:
	python -m pyflakes backend tests eval
