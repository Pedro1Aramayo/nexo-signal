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
