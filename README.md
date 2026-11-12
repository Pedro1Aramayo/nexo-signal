# NEXO SIGNAL

Detección de narrativas, posturas y operaciones coordinadas en cientos de miles de comentarios.
Proyecto para el **Desafío QualyData** (Big Data) de la Hackathon Argentina Space 2026.

El enunciado oficial, el formato de entrega y el puntaje están en [`DESAFIO.md`](DESAFIO.md).
La arquitectura propuesta está en [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) y el avance en
[`docs/BITACORA.md`](docs/BITACORA.md).

## Estado

Fase 1 (preparación): entorno reproducible, línea base oficial ejecutada y medida, arquitectura propuesta.
El pipeline propio todavía no está implementado.

| | Narrativas (/30) | Coordinación (/25) | Total (/55) |
|---|---|---|---|
| Línea base oficial | 12.52 | 9.44 | 21.96 |

## Cómo correr

Requisitos: Python 3.9+ y `make`.

```bash
make setup               # crea .venv e instala requirements-nexo.txt
make linea-base          # corre ejemplos/linea_base.py y registra tiempo/hardware en salida/practica_linea_base/medicion.json
make puntuar-linea-base  # corre evaluacion/puntuar.py y guarda salida/practica_linea_base/puntaje.json
```

## Qué existía antes del evento y qué hicimos nosotros

Preexistente (repositorio oficial `qualydata-org/desafio-qualydata`, commit `e727d18`), sin modificar:
`DESAFIO.md` (README oficial, solo renombrado), `datos/practica/`, `ejemplos/linea_base.py`,
`evaluacion/puntuar.py`, `requirements.txt`, `.gitignore`.

Desarrollado durante el evento: `README.md`, `Makefile`, `requirements-nexo.txt`, `herramientas/`, `docs/`.

Librerías públicas: numpy, pandas, scikit-learn, scipy, DuckDB, PyArrow.
