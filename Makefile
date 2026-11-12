PYTHON ?= python3
VENV   ?= .venv
PY     := $(VENV)/bin/python
DATOS  ?= datos/practica
VERDAD ?= $(DATOS)/verdad
LB_OUT ?= salida/practica_linea_base

.PHONY: setup linea-base puntuar-linea-base

setup:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements-nexo.txt

linea-base:
	$(PY) herramientas/medir.py --salida $(LB_OUT)/medicion.json --medir-dir $(LB_OUT) -- \
		$(PY) ejemplos/linea_base.py --datos $(DATOS) --entrega $(LB_OUT)

puntuar-linea-base:
	$(PY) evaluacion/puntuar.py --verdad $(VERDAD) --entrega $(LB_OUT) --json $(LB_OUT)/puntaje.json
