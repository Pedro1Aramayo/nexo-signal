PYTHON ?= python3
VENV   ?= .venv
PY     := $(VENV)/bin/python
DATOS  ?= datos/practica
VERDAD ?= $(DATOS)/verdad
LB_OUT ?= salida/practica_linea_base
NEXO_OUT ?= salida/practica_nexo

.PHONY: setup linea-base puntuar-linea-base nexo puntuar-nexo entrega diagnostico test

setup:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements-nexo.txt

linea-base:
	$(PY) herramientas/medir.py --salida $(LB_OUT)/medicion.json --medir-dir $(LB_OUT) -- \
		$(PY) ejemplos/linea_base.py --datos $(DATOS) --entrega $(LB_OUT)

puntuar-linea-base:
	$(PY) evaluacion/puntuar.py --verdad $(VERDAD) --entrega $(LB_OUT) --json $(LB_OUT)/puntaje.json

nexo:
	$(PY) herramientas/medir.py --salida $(NEXO_OUT)/medicion.json --medir-dir $(NEXO_OUT) -- \
		$(PY) -m nexo_signal --datos $(DATOS) --entrega $(NEXO_OUT) --cache .cache

puntuar-nexo:
	$(PY) evaluacion/puntuar.py --verdad $(VERDAD) --entrega $(NEXO_OUT) --json $(NEXO_OUT)/puntaje.json

entrega:
	$(PY) -m nexo_signal --datos $(DATOS) --entrega entrega --cache .cache

diagnostico:
	$(PY) -m nexo_signal.reporte.diagnostico --datos $(DATOS) --entrega $(NEXO_OUT)

test:
	$(PY) -m pytest -q
