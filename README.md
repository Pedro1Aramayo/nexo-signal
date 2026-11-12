# NEXO SIGNAL

Detección de narrativas, posturas y operaciones coordinadas en cientos de miles de comentarios.
Proyecto para el **Desafío QualyData** (Big Data) de la Hackathon Argentina Space 2026.

El enunciado oficial, el formato de entrega y el puntaje están en [`DESAFIO.md`](DESAFIO.md).
La arquitectura propuesta está en [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) y el avance en
[`docs/BITACORA.md`](docs/BITACORA.md).

## Estado

Fase 2: motor propio para agrupar comentarios por significado, estimar postura y detectar coordinación.

| | Narrativas (/30) | Coordinación (/25) | Total (/55) |
|---|---|---|---|
| Línea base oficial | 12.52 | 9.44 | 21.96 |

## Cómo correr

Requisitos: Python 3.10+ y `make`.

```bash
make setup               # crea .venv e instala requirements-nexo.txt
python -m nexo_signal --datos datos/practica --entrega salida/practica_nexo
make nexo                # corre el pipeline y registra la medición de tiempo/memoria
make puntuar-nexo        # puntúa salida/practica_nexo con la verdad del set de práctica
make diagnostico         # informa pureza, postura y confusión de ruido por cluster
make entrega DATOS=datos/final  # escribe la entrega final en entrega/
```

El comando directo es la forma de ejecución de una sola etapa. El pipeline guarda tablas limpias e
intermedias en `.cache/`, usa DuckDB + Parquet local y genera los cuatro archivos de entrega junto con
`metricas.json`. El modelo semántico corre localmente en CPU; no hay llamadas a servicios de IA.

Para puntuar otro directorio de salida, use `make puntuar-nexo NEXO_OUT=...`. La línea base sigue disponible:

```bash
make linea-base
make puntuar-linea-base
```

## Qué existía antes del evento y qué hicimos nosotros

Preexistente (repositorio oficial `qualydata-org/desafio-qualydata`, commit `e727d18`), sin modificar:
`DESAFIO.md` (README oficial, solo renombrado), `datos/practica/`, `ejemplos/linea_base.py`,
`evaluacion/puntuar.py`, `requirements.txt`, `.gitignore`.

Desarrollado durante el evento: `README.md`, `Makefile`, `requirements-nexo.txt`, `herramientas/`,
`docs/`, `nexo_signal/` y `tests/`.

Librerías públicas: numpy, pandas, scikit-learn, scipy, DuckDB, PyArrow, PyTorch,
Sentence Transformers, Transformers y NetworkX.
