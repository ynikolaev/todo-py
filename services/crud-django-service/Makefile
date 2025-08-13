# ===== Variables =====
PY           = poetry run python
POETRY       = poetry
MANAGE       = $(PY) src/manage.py
ifeq ($(OS),Windows_NT)
    VENVP := $(shell poetry env info --path)
    PYTHON := $(VENVP)\\Scripts\\python.exe
    ACTIVATE := $(VENVP)\\Scripts\\activate
else
    VENVP := $(shell poetry env info --path)
    PYTHON := $(VENVP)/bin/python
    ACTIVATE := $(VENVP)/bin/activate
endif


# ===== Poetry commands =====
.PHONY: install shell lock update export-reqs

install:            ## Install all dependencies
	$(POETRY) install

.PHONY: shell
shell:              ## Prints path to project env
	$(POETRY) env activate

lock:               ## Regenerate poetry.lock
	$(POETRY) lock

update:             ## Update all dependencies
	$(POETRY) update

export-reqs:        ## Export requirements.txt (no hashes)
	$(POETRY) export -f requirements.txt --output requirements.txt --without-hashes

# ===== Django management =====
.PHONY: run makemigrations migrate superuser shell-django collectstatic

run:                ## Run development server
	$(MANAGE) runserver

makemigrations:     ## Create new migrations
	$(MANAGE) makemigrations

migrate:            ## Apply migrations
	$(MANAGE) migrate

superuser:          ## Create a superuser
	$(MANAGE) createsuperuser

shell-django:       ## Django shell
	$(MANAGE) shell

collectstatic:      ## Collect static files
	$(MANAGE) collectstatic --noinput

# ===== Lint & test =====
.PHONY: lint format test

lint:               ## Run Ruff lint
	$(POETRY) run ruff check .

format:             ## Auto-format with Ruff
	$(POETRY) run ruff format .

test:               ## Run tests
	$(POETRY) run pytest

# ===== Helpers =====
.PHONY: help
help:               ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
