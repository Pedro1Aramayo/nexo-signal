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

## Dashboard NEXO SIGNAL

Requiere Node.js 20. Por defecto usa `datos/practica` y `salida/practica_nexo`. Para cambiar el
conjunto de datos (el modo final lee `datos/final` y `entrega`) y arrancar Vite:

```bash
make dashboard-datos CONJUNTO=practica # o CONJUNTO=final
make dashboard
```

### Probar la demo con el set final

1. `make setup && make descargar-final` (descarga el set final a `datos/final/`, no incluido en el repo)
2. `make entrega` (genera `entrega/` con los cuatro archivos oficiales) — o usar los ya commiteados
3. `make dashboard-datos CONJUNTO=final` (exporta los JSON del dashboard desde `datos/final` y `entrega`, sin modificar `entrega/`)
4. `make dashboard` y abrir http://localhost:5173

El dashboard muestra arriba «Datos: Set final QualyData (sintético)» para que quede claro qué conjunto está cargado.

Luego abre [http://localhost:5173](http://localhost:5173). El plan de integraciones futuras está en
[`docs/INTEGRACIONES.md`](docs/INTEGRACIONES.md).

### Qué es real y qué es demostración

- El motor y los resultados son reales y se ejecutan sobre datos sintéticos de QualyData.
- Las plataformas sociales se asignan solo para demostrar la interfaz; no hay cuentas conectadas.
- NEXO CONNECT y la autorización OAuth no están implementados (ver [`docs/INTEGRACIONES.md`](docs/INTEGRACIONES.md)).
- La clasificación por categorías es experimental: reglas heurísticas, precisión no medida.

### Limitaciones conocidas

**Asignación de narrativa en la operación G1 (set final).** NEXO ENGINE detectó G1 como un grupo coordinado de 52 cuentas y 363 comentarios, cuyos mensajes más repetidos apoyan la obra del dique («Sí a la obra: el dique es agua para la ciudad y para el riego»). Sin embargo, el motor asignó 240 de esos 363 comentarios a la narrativa n01, cuyo título es «Pongan luminarias en barrio Norte, de noche es boca de lobo.» y que en su mayoría trata sobre seguridad e iluminación (15.967 comentarios en total). Es un error de agrupamiento del motor: los textos de la campaña quedaron mezclados en una narrativa no relacionada. La detección del grupo y de sus cuentas no depende de esa asignación. No modificamos `entrega/` ni el motor después de la validación; el dashboard muestra la asignación tal como la produjo NEXO ENGINE.

## Qué existía antes del evento y qué hicimos nosotros

Preexistente (repositorio oficial `qualydata-org/desafio-qualydata`, commit `e727d18`), sin modificar:
`DESAFIO.md` (README oficial, solo renombrado), `datos/practica/`, `ejemplos/linea_base.py`,
`evaluacion/puntuar.py`, `requirements.txt`, `.gitignore`.

Desarrollado durante el evento: `README.md`, `Makefile`, `requirements-nexo.txt`, `herramientas/`,
`docs/`, `nexo_signal/` y `tests/`.

Librerías públicas: numpy, pandas, scikit-learn, scipy, DuckDB, PyArrow, PyTorch,
Sentence Transformers, Transformers y NetworkX.
