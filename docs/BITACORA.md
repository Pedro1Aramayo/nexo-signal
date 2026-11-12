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

## 2026-11-12 — Fase 2: NEXO ENGINE

### Investigación (scripts exploratorios fuera del repo; la verdad de práctica solo se usó para medir)

- Embeddings de los 112k textos únicos: 375 s en CPU. Con núcleos (sin muletillas aprendidas del corpus): 15.8k únicos, ~25 s.
- Embeddings crudos agrupan mal (KMeans 13: F1 0.35): aperturas, cierres y emojis dominan la similitud.
- Grafo semántico de núcleos + aristas de respuesta + Louvain: B-cubed F1 0.949 (sin aristas de respuesta: 0.19).
- Respuestas: siempre misma narrativa que el padre; las cortas heredan la postura; las largas la contradicen ~96%.
- Coordinación: ninguna señal de pares discrimina sola (C2 usa cuentas viejas y textos variados). La señal está a
  nivel grupo: densidad interna muy por encima de lo esperable.

### v1 (commit `63a1d1c`) — primera versión completa

| Métrica | Línea base | v1 |
|---|---|---|
| Agrupamiento B-cubed P / R / F1 | 0.424 / 0.282 / 0.339 | 0.992 / 0.534 / **0.694** |
| Ruido F1 | 0.665 | 0.514 |
| Postura macro-F1 | 0.491 | 0.383 |
| Origen de emergentes | 0.333 | 0.333 |
| Narrativas | 12.52 / 30 | **16.53 / 30** |
| Cuentas coordinadas P / R / F1 | 1.000 / 0.304 / 0.467 | 0.409 / 0.922 / 0.567 |
| Grupos B-cubed F1 | 0.169 | **0.930** |
| Coordinación | 9.44 / 25 | **16.90 / 25** |
| **Total** | **21.96 / 55** | **33.43 / 55** |

Tiempo 65 s, memoria pico 2.9 GB, USD IA 0 (con caché de embeddings caliente).

Diagnóstico de v1:
- Ruido: un solo núcleo marcado como ruido arrastraba a todo su grupo (71k falsos positivos) → error de implementación.
- Postura: orientar por "qué lado aparece primero" falla en 3 de 10 grupos (en la verdad ambos lados arrancan parejos).
  Se reemplaza por marcadores genéricos de refutación del español (en práctica, el lado que rechaza tiene más en 13/13).
- Coordinación: 2 grupos falsos sostenidos solo por frases comunes compartidas **una vez**. Se exige repetición
  (≥2 coincidencias de texto por par), como ya se exigía en co-publicación.
