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
make entrega             # procesa datos/final y escribe la entrega final
make validar             # valida el formato de entrega contra datos/final
```

El comando directo es la forma de ejecución de una sola etapa. El pipeline guarda tablas limpias e
intermedias en `.cache/`, usa DuckDB + Parquet local y deja exactamente los cuatro archivos oficiales
en la raíz de salida; las métricas, mediciones y evidencia de coordinación quedan en `evidencia/`.
El modelo semántico corre localmente en CPU; no hay llamadas a servicios de IA.

Para puntuar otro directorio de salida, use `make puntuar-nexo NEXO_OUT=...`. La línea base sigue disponible:

```bash
make linea-base
make puntuar-linea-base
```

## Reproducir la entrega

```bash
make setup && make descargar-final && make entrega && make validar
```

Sobre el set final (150.000 comentarios), `make entrega` tarda unos 65 s (2,9 GB de memoria pico) en una
máquina CPU de 8 núcleos y unos 31 GB de RAM, sin GPU. Se verificó desde un clon limpio con caché vacía:
los tres CSV coinciden byte a byte con los commiteados en `entrega/`. Los SHA-256 de los archivos descargados coincidieron con los publicados en
las notas del release `set-final`. La primera ejecución descarga cerca de 470 MB desde
Hugging Face, usando la revisión fijada del modelo. `datos/final/` se descarga desde el release
`set-final` y no está incluido en el repositorio. La carpeta `entrega/` conserva en su raíz solo los
cuatro archivos oficiales; las mediciones y demás evidencia se guardan en `entrega/evidencia/`.

## Dashboard (Fase 3, en desarrollo)

Requiere Node.js 20. La demo usa `datos/practica` y la salida de práctica generada con `make nexo`;
no hay cuentas conectadas. Para preparar los datos y arrancar Vite:

```bash
make dashboard-datos && make dashboard
```

Luego abre [http://localhost:5173](http://localhost:5173). El plan de integraciones futuras está en
[`docs/INTEGRACIONES.md`](docs/INTEGRACIONES.md).

## Qué existía antes del evento y qué hicimos nosotros

Preexistente (repositorio oficial `qualydata-org/desafio-qualydata`, commit `e727d18`), sin modificar:
`DESAFIO.md` (README oficial, solo renombrado), `datos/practica/`, `ejemplos/linea_base.py`,
`evaluacion/puntuar.py`, `requirements.txt`, `.gitignore`.

Desarrollado durante el evento: `README.md`, `Makefile`, `requirements-nexo.txt`, `herramientas/`,
`docs/`, `nexo_signal/` y `tests/`.

Librerías públicas: numpy, pandas, scikit-learn, scipy, DuckDB, PyArrow, PyTorch,
Sentence Transformers, Transformers y NetworkX.
