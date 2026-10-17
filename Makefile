.PHONY: help setup sync age db-start db-stop load lint format check typecheck \
        test test-cov notebooks run lab clean reset ci dev

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## First-time setup (Python env)
	@command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
	uv sync --all-extras
	uv run python -m ipykernel install --user --name apache-age-101
	@echo "\n✅ Python ready. Now run 'make age' then 'make load' then 'make test'."

sync: ## Sync deps
	uv sync --all-extras

age: ## One-time: install local Postgres + build Apache AGE + CREATE EXTENSION (local only)
	bash scripts/install_age.sh
	@echo "✅ Local Postgres with Apache AGE ready (no cloud, no account)."

db-start: ## Start the local Postgres service
	sudo service postgresql start || pg_ctl -D $$PGDATA start

db-stop: ## Stop the local Postgres service
	sudo service postgresql stop || pg_ctl -D $$PGDATA stop

load: ## Generate graphs and load them into AGE (+ relational tables for the SQL baseline)
	uv run python -m src.datasets.graphs
	uv run python -m src.age.load
	@echo "✅ Graphs loaded into AGE and relational tables."

lint: format check typecheck ## All linters
format: ## ruff format
	uv run ruff format src/ tests/ app/
check: ## ruff check
	uv run ruff check --fix src/ tests/ app/
typecheck: ## ty check
	uv run ty check src/

test: ## pytest
	uv run pytest
test-cov: ## pytest with coverage
	uv run pytest --cov=src --cov-report=term-missing

notebooks: ## Execute all notebooks
	@for nb in notebooks/0*.ipynb; do \
		echo "▶ Executing $$nb ..."; \
		uv run jupyter nbconvert --to notebook --execute \
			--ExecutePreprocessor.timeout=360 "$$nb" || exit 1; \
	done
	@echo "\n✅ All notebooks executed."

run: ## Streamlit app
	uv run streamlit run app/streamlit_app.py --server.port 8501
lab: ## JupyterLab
	uv run jupyter lab --no-browser --port 8888

clean: ## Clean
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache htmlcov .coverage .pytest_cache .ruff_cache
	@echo "🧹 Cleaned."
reset: clean ## Full reset (keeps the DB)
	rm -rf .venv

ci: sync lint test ## CI
dev: lint test ## Fast loop
