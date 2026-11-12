# NEXO SIGNAL — Arquitectura propuesta

Objetivo: un pipeline CPU-first, reproducible y sin supuestos sobre el tema, que corra de punta a punta con
**un solo comando** y genere `entrega/` (comentarios, narrativas, cuentas, costo).

## Diagnóstico de la línea base (set de práctica)

| Componente | Línea base | Qué falla | Señal que vamos a usar |
|---|---|---|---|
| Agrupamiento (B-cubed F1) | 0.339 | k fijo = 20 sobre TF-IDF: mezcla narrativas del mismo tema (L3/L4/L5/H3/H4 caen en un mismo grupo) y parte otras. | Embeddings semánticos + clustering por densidad que decide el número de grupos solo. |
| Ruido (F1) | 0.665 | Solo usa "menos de 4 palabras". Las preguntas operativas ("¿a qué hora pasa la última?") y las respuestas cortas que acompañan ("Clarísimo", que heredan narrativa) quedan mal. | Distancia a los núcleos de narrativa + forma (pregunta, reacción, emoji) + herencia por `respuesta_a`. |
| Postura (macro-F1) | 0.491 | Lista de palabras. El 48% de los comentarios con narrativa rechaza, casi siempre con contraste ("se frenó por falta de materiales, **no por robo**"). | Postura relativa al prototipo de cada narrativa + patrones de negación/contraste + propagación en hilos de respuesta. |
| Origen de emergentes | 0.333 | Cuantil 1% de un grupo impuro: cae antes del origen real. | Detección de cambio de régimen (primer pico sostenido) sobre los comentarios con alta pertenencia al grupo. |
| Cuentas coordinadas (F1) | 0.467 (P=1.0, R=0.30) | Solo texto idéntico + ráfaga: no ve a C2 (textos variados) ni a casi toda C3. | Grafo de co-acción con repetición y comparación contra lo esperable + perfil de cuenta. |
| Grupos por operación (B-cubed F1) | 0.169 | Una campaña queda partida en varios grupos chicos. | Detección de comunidades sobre el grafo ponderado. |

Lo que muestran los datos:
- 200.000 comentarios, pero solo **112.340 textos distintos**: deduplicar antes de vectorizar reduce el costo ~44%.
- 18,9% es ruido; el 57% del ruido tiene menos de 20 caracteres, el resto son preguntas o comentarios fuera de tema.
- 14% de los comentarios son respuestas (`respuesta_a`): las respuestas cortas heredan narrativa y postura.
- Campañas con estilos distintos: C1 (cuentas nuevas, plantilla + hashtag, ráfagas diurnas), C2 (cuentas
  antiguas, textos variados, mismas publicaciones, se responden entre sí), C3 (cuentas nuevas, ráfagas nocturnas
  que originan la narrativa). Ninguna señal sola alcanza: hace falta combinarlas.

## Estructura de módulos

```
nexo_signal/
  __main__.py              # python -m nexo_signal --datos datos/final --entrega entrega   (un solo comando)
  config.py                # parámetros generales; sin narrativas ni cantidades de campañas fijas
  ingesta/
    cargar.py              # CSV.gz -> validación y limpieza (encoding, fechas, ids, duplicados) -> Parquet
    almacen.py             # DuckDB sobre Parquet: vistas y consultas analíticas
  texto/
    normalizar.py          # minúsculas, acentos, emojis, alargamientos, abreviaturas, hashtags, menciones
    embeddings.py          # modelo multilingüe chico local (CPU/ONNX), batch, caché en Parquet por hash de texto
    duplicados.py          # MinHash/SimHash para casi-duplicados (sirve a ruido y a coordinación)
  narrativas/
    ruido.py               # puntaje de ruido: forma + distancia a núcleos + herencia en respuestas
    agrupar.py             # reducción + clustering por densidad (k automático) + fusión de grupos que derivan en el tiempo
    postura.py             # postura respecto del prototipo de la narrativa, negación/contraste, hilos de respuesta
    origen.py              # fecha de origen por cambio de régimen temporal
    describir.py           # títulos y frases clave (c-TF-IDF); IA opcional solo para nombrar grupos
  coordinacion/
    senales.py             # por cuenta: antigüedad, seguidores/siguiendo, horario, casi-duplicados, hashtags propios
    grafo.py               # co-acción (misma publicación + ventana corta + repetición) y respuestas mutuas,
                           # ponderado contra lo esperable según la actividad de cada publicación
    comunidades.py         # Louvain/Leiden + filtro por anomalía -> grupos por operación
  reporte/
    costo.py               # costo.json: tiempo, hardware, almacenamiento, tokens y USD reales
    diagnostico.py         # métricas por narrativa/campaña usando evaluacion/puntuar.py (sin modificarlo)
tests/                     # pruebas con datos sucios y chicos
```

Flujo: `ingesta -> texto -> narrativas (ruido, agrupar, postura, origen, describir) -> coordinacion -> reporte`.
Cada etapa escribe Parquet intermedio en `salida/<corrida>/cache/` para poder reanudar y medir por etapa.

## Implementación Fase 2 — NEXO ENGINE (lo que corre hoy)

Comando único: `python -m nexo_signal --datos <carpeta> --entrega <carpeta>` (o `make nexo` / `make entrega`).

**Narrative DNA**
1. *Núcleo del comentario.* Normalización (minúsculas, sin acentos/emojis/URLs, alargamientos colapsados) y
   eliminación de muletillas de apertura/cierre **aprendidas del propio corpus** (segmentos de borde muy frecuentes
   y combinados con contenidos muy distintos). 200k comentarios → ~16k núcleos únicos: solo esos se vectorizan.
2. *Embeddings locales.* `paraphrase-multilingual-MiniLM-L12-v2` en CPU, caché en disco por hash del núcleo.
3. *Agrupamiento sin k fijo.* Grafo de núcleos: k-vecinos semánticos (coseno ≥ 0.6) + aristas por respuestas largas
   (una respuesta discute la misma afirmación que su padre, aunque la contradiga). Louvain decide la cantidad de grupos.
   Sin las aristas de respuesta, apoyo y rechazo de una misma narrativa quedan en grupos distintos.
4. *Ruido por interacción.* Los comentarios de una narrativa generan conversación; el ruido no. Se marca ruido a nivel
   núcleo (test binomial contra la tasa global de interacción) y a nivel grupo (interacción < 25% de la global).
5. *Postura.* Dentro de cada narrativa, partición firmada: similitud semántica une, respuesta larga separa
   (las respuestas largas contradicen a su padre). El autovector principal da los dos lados; el lado con mayor
   tasa de marcadores genéricos de refutación ("falso", "pero", "no es", "pruebas"…) es *rechaza*.
6. *Respuestas cortas* ("Tal cual", "Exacto"): heredan narrativa y postura del comentario original; se invierte la
   postura si la respuesta expresa desacuerdo.
7. *Origen.* Primer instante con actividad sostenida del grupo (mínimo de comentarios en una ventana de 6 h).
8. *Descripción.* Título = núcleo más frecuente del lado que apoya; frases clave por c-TF-IDF.

**Coordination Fingerprint**
1. *Señales de pares de cuentas* (DuckDB): co-publicación en la misma publicación con ≤10 min de diferencia en ≥2
   publicaciones distintas; mismo texto (núcleo ≥25 caracteres) con ≤2 h de diferencia repetido ≥2 veces; respuestas entre sí.
2. *Candidatos:* comunidades Louvain del grafo sincronía+texto y del k-truss (k=3) del grafo de respuestas
   (operaciones que no copian texto pero se responden entre sí).
3. *Coordinación vs. viralidad:* un grupo se acepta si su densidad interna ≥ 0.3 **y** supera ≥10× lo esperable por el
   modelo de configuración (las cuentas muy activas o una publicación viral generan muchas coincidencias, pero
   repartidas; una operación las concentra en un grupo chico).
4. *Expansión:* se suman cuentas con varias conexiones al grupo que representan una fracción grande de su actividad.
5. *Evidencia complementaria* por grupo (`grupos_coordinados.csv`): antigüedad de las cuentas, seguidores, horario
   nocturno, publicaciones; sirve para explicar y auditar, no decide la detección.

Ninguna regla menciona temas, narrativas o campañas del set de práctica; los umbrales son relativos
(tasas globales, modelo nulo) para trasladarse a datos nuevos.

## Decisiones técnicas

- **Almacenamiento: DuckDB + Parquet.** Columnar, comprimido, sin servidor, SQL analítico rápido en una notebook y
  escalable a particiones por día (`fecha=YYYY-MM-DD/`) para millones de comentarios diarios.
- **Embeddings locales.** Candidatos: `paraphrase-multilingual-MiniLM-L12-v2` o `multilingual-e5-small`
  (~120M parámetros, CPU). Se calcula una vez por texto único y se cachea. Se elige el modelo midiendo calidad vs. tiempo.
- **k automático.** HDBSCAN (o aglomerativo con umbral) sobre embeddings reducidos; los grupos chicos o difusos van a ruido.
- **Postura sin API por comentario.** Señales de negación/contraste y comparación con el prototipo de la narrativa;
  opcional: clasificador liviano entrenado con la verdad de práctica, validado entre temas.
- **IA generativa: opcional y acotada** (nombrar narrativas, ~1 llamada por grupo). Tokens y USD van a `costo.json`.

## Protocolo de validación (para generalizar al set final)

- El set final tiene otros temas. Todo parámetro o modelo que se ajuste con la verdad de práctica se valida
  **dejando un tema afuera** (litio / colectivo / hospital) para no sobreajustar.
- Cada cambio se compara contra la línea base con `evaluacion/puntuar.py` y se registra en `docs/BITACORA.md`.
- Semillas fijas y versiones fijadas (`requirements-nexo.txt`) para que la corrida sea reproducible.

## Reglas que respeta el diseño

- Sin etiquetas manuales sobre el set final; sin narrativas ni cantidades de campañas predefinidas.
- Sin llamadas a una API de IA por comentario; todo el motor corre en CPU.
- `evaluacion/puntuar.py` no se modifica.
- Lo preexistente y lo desarrollado durante el evento queda registrado en el README y en la bitácora.

## Visión de producto (posterior al desafío, no implementado)

El motor (`nexo_signal`) se diseña como núcleo reutilizable: todo lo de abajo consume sus salidas (narrativas, postura, cuentas y grupos coordinados) sin reprocesar texto.

### NEXO SIGNAL — dashboard interactivo
- Mapa de narrativas: tamaño, título, frases clave, balance apoya/rechaza y curva temporal desde la fecha de origen.
- Drill-down a comentarios representativos y a la cadena de respuestas que originó cada narrativa.
- Alertas cuando aparece una narrativa nueva (cambio de régimen) o cuando una existente se acelera.
- Base técnica: los Parquet de salida + DuckDB como motor de consulta; API liviana encima y frontend web.

### ORGANIC LENS — actividad total vs. orgánica
- Toda métrica (volumen por narrativa, postura, picos temporales) se muestra dos veces: con todas las cuentas y excluyendo las cuentas marcadas por Coordination Fingerprint.
- La diferencia cuantifica cuánto de una conversación está inflado por operaciones coordinadas.
- Cada grupo coordinado expone su evidencia (densidad, ratio contra lo esperable, canal: sincronía/texto o respuestas, antigüedad y horarios) para que la exclusión sea auditable y no una caja negra.

### NEXO CONNECT — integración con Instagram
- Conexión de cuentas profesionales mediante la API oficial de Meta (Instagram Graph API) con OAuth y permisos explícitos del titular; sin scraping.
- Ingesta periódica de comentarios de las publicaciones propias hacia el mismo formato de `datos/` y clasificación automática por categorías/narrativas con el motor.
- Requisitos a resolver antes de implementar: revisión de app de Meta, límites de tasa, retención y borrado de datos, y consentimiento.

Prioridad: ninguna de estas piezas se implementa hasta cerrar la entrega del desafío.
