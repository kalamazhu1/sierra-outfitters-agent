PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
PY := $(BIN)/python

.PHONY: help install web chat test clean

help:
	@echo "Sierra Outfitters Agent"
	@echo ""
	@echo "Commands:"
	@echo "  make install  Create .venv and install dependencies"
	@echo "  make web      Start the web UI at http://127.0.0.1:5001"
	@echo "  make chat     Start the terminal chat"
	@echo "  make test     Run the test suite"
	@echo "  make clean    Remove Python caches"

$(PY):
	$(PYTHON) -m venv $(VENV)

install: $(PY)
	$(PIP) install -r requirements.txt
	@test -f .env || cp .env.example .env

web: install
	$(PY) web_app.py

chat: install
	$(PY) main.py

test: install
	$(PY) -m pytest -q

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf .pytest_cache
