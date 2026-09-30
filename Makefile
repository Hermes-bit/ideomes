# Raccourcis (Linux / macOS / WSL). Sous Windows : scripts/dev.ps1
PY ?= python

install:
	$(PY) -m pip install -r requirements.txt
	$(PY) -m pip install -e agents

web:
	$(PY) web/build.py

api: web
	cd api && $(PY) -m uvicorn app.main:app --reload --port 8000

seed:
	$(PY) scripts/seed.py

demo:
	ideomes demo

test:
	cd agents && $(PY) -m pytest -q
	cd api && $(PY) -m pytest -q

eval:
	ideomes eval

veille:
	ideomes veille

lint:
	ruff check agents api scripts web/build.py
