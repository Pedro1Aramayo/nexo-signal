PYTHON ?= python3
VENV   ?= .venv
PY     := $(VENV)/bin/python
DATOS  ?= datos/practica
VERDAD ?= $(DATOS)/verdad
DATOS_FINAL ?= $(if $(filter command line environment override,$(origin DATOS)),$(DATOS),datos/final)
LB_OUT ?= salida/practica_linea_base
NEXO_OUT ?= salida/practica_nexo
ENTREGA_OUT ?= entrega
CACHE ?= .cache
CONJUNTO ?= practica

.PHONY: setup linea-base puntuar-linea-base nexo puntuar-nexo entrega descargar-final validar demo dashboard-datos dashboard diagnostico test

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
	$(PY) herramientas/medir.py --salida $(NEXO_OUT)/evidencia/medicion.json --costo $(NEXO_OUT)/costo.json --medir-dir $(NEXO_OUT) -- \
		$(PY) -m nexo_signal --datos $(DATOS) --entrega $(NEXO_OUT) --cache $(CACHE)

puntuar-nexo:
	$(PY) evaluacion/puntuar.py --verdad $(VERDAD) --entrega $(NEXO_OUT) --json $(NEXO_OUT)/evidencia/puntaje.json

entrega:
	$(PY) herramientas/medir.py --salida $(ENTREGA_OUT)/evidencia/medicion.json --costo $(ENTREGA_OUT)/costo.json --medir-dir $(ENTREGA_OUT) -- \
		$(PY) -m nexo_signal --datos $(DATOS_FINAL) --entrega $(ENTREGA_OUT) --cache $(CACHE)

descargar-final:
	bash herramientas/descargar_final.sh

validar:
	$(PY) -m herramientas.validar_entrega --datos $(DATOS_FINAL) --entrega $(ENTREGA_OUT)

demo:
	$(PY) herramientas/demo.py --datos $(DATOS_FINAL) --entrega $(ENTREGA_OUT) --salida docs/demo/nexo_signal.html

dashboard-datos:
	$(PY) herramientas/exportar_dashboard.py --conjunto $(CONJUNTO) --salida dashboard/public/data

dashboard:
	cd dashboard && npm install && npm run dev

diagnostico:
	$(PY) -m nexo_signal.reporte.diagnostico --datos $(DATOS) --entrega $(NEXO_OUT)

test:
	$(PY) -m pytest -q
