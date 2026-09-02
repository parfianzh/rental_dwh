PYTHON := venv/bin/python
RUNNER := rental_dwh.extract.extract_runner
TRANSFORM_RUNNER := rental_dwh.transform.transform_runner
DATE ?= $(shell date +%F)
LOAD_RUNNER := rental_dwh.load.load_runner

.PHONY: help \
	extract_etagi extract_kvartirant extract_yandex_realty \
	transform_etagi transform_kvartirant transform_yandex_realty \
	match_listings \
	load_dwh

help:
	@echo "make extract_etagi"
	@echo "make extract_kvartirant"
	@echo "make extract_yandex_realty"
	@echo "make transform_etagi"
	@echo "make transform_kvartirant"
	@echo "make transform_yandex_realty"
	@echo "make match_listings"
	@echo "make load_dwh"

extract_etagi:
	PYTHONPATH=src $(PYTHON) -m $(RUNNER) etagi

extract_kvartirant:
	PYTHONPATH=src $(PYTHON) -m $(RUNNER) kvartirant

extract_yandex_realty:
	PYTHONPATH=src $(PYTHON) -m $(RUNNER) yandex_realty

transform_etagi:
	PYTHONPATH=src $(PYTHON) -c "from $(TRANSFORM_RUNNER) import run; print(run('etagi', 'data/raw/etagi/$(DATE).csv', 'data/processed/etagi/$(DATE).json'))"

transform_kvartirant:
	PYTHONPATH=src $(PYTHON) -c "from $(TRANSFORM_RUNNER) import run; print(run('kvartirant', 'data/raw/kvartirant/$(DATE).json', 'data/processed/kvartirant/$(DATE).json'))"

transform_yandex_realty:
	PYTHONPATH=src $(PYTHON) -c "from $(TRANSFORM_RUNNER) import run; print(run('yandex_realty', 'data/raw/yandex_realty/$(DATE).json', 'data/processed/yandex_realty/$(DATE).json'))"

match_listings:
	PYTHONPATH=src $(PYTHON) -c "from $(TRANSFORM_RUNNER) import match_listings; print(match_listings(['data/processed/etagi/$(DATE).json', 'data/processed/kvartirant/$(DATE).json', 'data/processed/yandex_realty/$(DATE).json'], 'data/processed/matched/$(DATE).json'))"

load_dwh:
	PYTHONPATH=src $(PYTHON) -c "from datetime import datetime; from $(LOAD_RUNNER) import run; started_at = datetime.now().astimezone(); print(run(['data/processed/etagi/$(DATE).json', 'data/processed/kvartirant/$(DATE).json', 'data/processed/yandex_realty/$(DATE).json'], 'data/processed/matched/$(DATE).json', 'manual__' + started_at.isoformat(), started_at))"
