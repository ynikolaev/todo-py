install:
	python -m pip install --upgrade pip
	pip install -r requirements-dev.txt

gen-req:
	poetry export -f requirements.txt --output requirements.txt --without-hashes

venv:
	python -m venv .venv
	. .venv/bin/activate && make install