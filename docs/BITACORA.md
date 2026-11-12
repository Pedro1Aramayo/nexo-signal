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

### v2 (commit `5ca74d4`) — correcciones de ruido, postura y coordinación

| Métrica | Línea base | v1 | v2 |
|---|---|---|---|
| Agrupamiento B-cubed F1 | 0.339 | 0.694 | **0.956** (P 0.983 / R 0.931) |
| Ruido F1 | 0.665 | 0.514 | **0.977** |
| Postura macro-F1 | 0.491 | 0.383 | **0.990** |
| Origen de emergentes | 0.333 | 0.333 | 0.667 (L5 0, B4 1, H3 1) |
| Narrativas | 12.52 | 16.53 | **27.68 / 30** |
| Cuentas coordinadas P / R / F1 | 1.00 / 0.30 / 0.47 | 0.41 / 0.92 / 0.57 | **0.97 / 0.92 / 0.95** (109 marcadas) |
| Grupos B-cubed F1 | 0.169 | 0.930 | 0.930 |
| Coordinación | 9.44 | 16.90 | **23.54 / 25** |
| **Total** | **21.96** | **33.43** | **51.22 / 55** |

51 s, 2.7 GB pico, USD 0. Dos corridas con salida idéntica byte a byte (md5).

### v3 (commit `ed4c760`) — origen por cambio de régimen y piso de tamaño

- Origen: primer instante cuya ventana de 6 h alcanza el 10% del pico del propio grupo (antes, unos pocos comentarios
  sueltos adelantaban el origen de L5 seis días). Grupos con < 30 comentarios no cortos pasan a ruido.
- Práctica: origen 0.771 (L5 1.0, B4 1.0, H3 0.31) → **51.69 / 55** (narrativas 28.15, coordinación 23.54). 57 s, 2.6 GB.
- Costo de la regla: H3 (arranque chico de una campaña nocturna) ahora se fecha más tarde.

### Prueba de generalización: un tema por vez (`herramientas/subconjuntos.py`)

Cada tema de práctica como dataset independiente, sin reajustar nada:

| Tema | Comentarios | Narrativas detectadas | Narrativas / Coordinación / Total |
|---|---:|---:|---:|
| colectivo (sin campañas) | 64.742 | 15 | 26.37 / 0.71 / 27.08 |
| hospital | 58.020 | 22 | 21.82 / 12.47 / 34.29 |
| litio | 77.238 | 24 | 23.80 / 22.36 / 46.16 |

Hallazgo: con datasets más chicos el agrupamiento parte narrativas (recall 0.51–0.70). Hipótesis: la resolución de
Louvain (modularidad) depende del tamaño del grafo. En estudio.

Barrido de resolución de Louvain (B-cubed F1 del agrupamiento; misma configuración en todo lo demás):

| Resolución | litio (77k) | hospital (58k) | práctica completa (200k) |
|---|---|---|---|
| 0.50 | 0.666 (24 grupos) | 0.709 (22) | 0.956 (19) |
| 0.25 | 0.914 (11) | 0.957 (12) | 0.971 (15) |
| 0.15 | 0.931 (8) | 0.990 (9) | 0.968 (15) |
| 0.10 | **0.950** (7) | **0.990** (9) | **0.974** (14) |
| 0.05 | 0.950 (7) | 0.995 (8) | — |

Confirmado: con 0.5 el resultado dependía del tamaño del dataset. Con 0.10 la precisión casi no cambia
(0.96–0.99) y el recall queda estable entre 58k y 200k comentarios. Se adopta 0.10.
