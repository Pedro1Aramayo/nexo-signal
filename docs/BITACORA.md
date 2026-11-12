# Bitácora de desarrollo — NEXO SIGNAL

Registro de lo hecho durante la Hackathon Argentina Space 2026 (11 al 13 de noviembre de 2026).

## 2026-11-12 — Fase 1: preparación y evaluación inicial

- Clonado el repositorio oficial `qualydata-org/desafio-qualydata` (commit `e727d18`) como base de `nexo-signal`.
  El README oficial se conserva como `DESAFIO.md`.
- Entorno: Python 3.10.12, venv, versiones fijadas en `requirements-nexo.txt`.
- Agregados: `Makefile`, `herramientas/medir.py` (tiempo, CPU, memoria pico, hardware, almacenamiento),
  `docs/ARQUITECTURA.md`, esta bitácora.
- Línea base oficial ejecutada dos veces con salida idéntica (determinista).

### Línea base oficial — set de práctica

Hardware: VM Linux, Intel Xeon 8 núcleos, 31 GB RAM, sin GPU.
Tiempo: 16,4 s reloj / 21,8 s CPU; memoria pico 504 MB; salida 3,8 MB; USD IA 0.

| Métrica | Valor |
|---|---|
| Agrupamiento B-cubed P / R / F1 | 0.424 / 0.282 / **0.339** |
| Ruido F1 | **0.665** |
| Postura macro-F1 | **0.491** |
| Origen de emergentes | **0.333** (L5 0.0, B4 1.0, H3 0.0) |
| Narrativas | **12.52 / 30** |
| Cuentas coordinadas P / R / F1 | 1.000 / 0.304 / **0.467** (35 marcadas de 115) |
| Grupos B-cubed F1 | **0.169** |
| Coordinación | **9.44 / 25** |
| **Total automático** | **21.96 / 55** |

Nota: el README oficial menciona ~17 puntos; con las versiones fijadas de este entorno da 21.96 de forma estable.
