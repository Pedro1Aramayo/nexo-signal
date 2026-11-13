# NEXO SIGNAL — material para video y pitch (Hacki)

## Mensaje central (1 frase)
NEXO SIGNAL lee cientos de miles de comentarios en aproximadamente 65 segundos (tiempo de reloj medido en una CPU de 8 núcleos, sin GPU) y sin llamadas a servicios comerciales de IA. Encuentra qué se está diciendo, quién apoya y quién rechaza, cuándo empezó cada narrativa y qué parte de la conversación está impulsada por operaciones coordinadas.

**Cifras de costo, para no confundir:** los 65 s (`segundos: 64.96` en `entrega/costo.json`) se midieron sobre los 150.000 comentarios del set final en una máquina Intel Xeon de 8 núcleos, 31 GB de RAM y sin GPU. «USD 0» corresponde a llamadas comerciales de IA (`usd_ia: 0`, `tokens_ia: 0`); no es el costo total, porque no incluye el hardware.

## Guion del video: recorrido del dashboard (2–3 minutos)

Este es el guion principal. Grabar con el dashboard React corriendo sobre el **set final**:

```bash
make dashboard-datos CONJUNTO=final
make dashboard
```

| Tiempo | Pantalla | Qué decir |
|---|---|---|
| 0:00–0:20 | Inicio | «NEXO SIGNAL analizó 150.000 comentarios del set final de QualyData en 372 publicaciones y 8 fuentes, con un solo comando: unos 65 segundos de reloj en una CPU de 8 núcleos, sin GPU, y USD 0 en llamadas a servicios comerciales de IA.» Señalar el resumen de la derecha: 150.000 comentarios, 12 narrativas, 94 cuentas coordinadas, 3 operaciones. |
| 0:20–0:40 | Inicio · filtros | Tocar Instagram, TikTok y X. «Las plataformas son una demostración de la interfaz: los datos son sintéticos y ninguna cuenta está conectada.» Usar el buscador y el orden por «más comentadas». |
| 0:40–1:10 | Publicación | «Analizar publicación» en una publicación con coordinación. Mostrar los comentarios reales y los botones de categoría: consultas, quejas, elogios, sugerencias y otros. «Esta clasificación comercial es experimental: reglas heurísticas, precisión no medida.» Filtrar por quejas. |
| 1:10–1:35 | Publicación · narrativas | Mostrar las narrativas detectadas con su barra de apoyo y rechazo. «Las narrativas no están definidas de antemano: el motor las descubre y después clasifica la postura de cada comentario.» Tocar una narrativa para filtrar sus comentarios. |
| 1:35–2:00 | Organic Lens | Elegir una narrativa. «Organic Lens separa la actividad total de la actividad sin coordinación detectada, día por día. Excluir la coordinación detectada no garantiza que el resto sea genuino: solo descuenta las cuentas que el motor marcó.» |
| 2:00–2:35 | Coordinación · G3 | Bajar hasta la operación G3. «21 cuentas, 84 comentarios en 6 publicaciones, 100% de actividad nocturna y cuentas creadas 5 días antes de comentar. Los mensajes más repetidos piden compartir el cierre de la comisaría, y el motor asignó el 100% de esos comentarios a la narrativa correspondiente: coordinación, no viralidad.» |
| 2:35–3:00 | Cierre | «En el set de práctica, con el evaluador oficial, NEXO ENGINE saca 51.65 sobre 55, contra 21.96 de la línea base: agrupamiento 0.97, ruido 0.96 y postura 0.99 de F1. Lo implementado es el motor y este dashboard. Lo que sigue es NEXO CONNECT: conectar cuentas reales con OAuth oficial, todavía no implementado.» |

**Implementado:** descubrimiento de narrativas, postura, ruido, fecha de origen, detección de operaciones coordinadas, Organic Lens, dashboard navegable y entrega reproducible con un comando.

**Todavía no implementado:** NEXO CONNECT y la autorización OAuth con las APIs oficiales (plan en [`INTEGRACIONES.md`](INTEGRACIONES.md)). La clasificación por categorías es experimental. Ver «Limitaciones conocidas» en el README (operación G1).

La demo HTML estática (`make demo`, `docs/demo/nexo_signal.html`) queda solo como respaldo y no forma parte del video.

## Pitch (slides)
1. **Problema y por qué importa:** desinformación, campañas, reputación.
2. **Arquitectura en una imagen:**
   - CSV.gz → DuckDB/Parquet → normalización;
   - núcleos únicos (200k → 16k) → embeddings locales en CPU con caché;
   - grafo semántico + respuestas → Louvain;
   - ruido por falta de interacción;
   - postura por autovector firmado;
   - origen por cambio de régimen;
   - coordinación con señales de pares en DuckDB, grafos, k-truss y modelo nulo;
   - salida en `entrega/` y demo.
3. **Resultados en práctica** (evaluador oficial sin modificar):

   | | Línea base | NEXO |
   |---|---|---|
   | Narrativas /30 | 12.52 | 28.11 |
   | Coordinación /25 | 9.44 | 23.54 |
   | Total /55 | 21.96 | 51.65 |
   | Tiempo (200k, práctica) | 16 s | ~50–107 s |
   | USD en llamadas comerciales de IA | 0 | 0 |

   **Set final (sin verdad, 150.000 comentarios):** 12 narrativas, 19,5% de ruido, 3 operaciones coordinadas (94 cuentas: 52 con texto repetido sincronizado, 21 de cuentas antiguas en red de respuestas, 21 nocturnas en una sola publicación), unos 65 s de reloj en una CPU de 8 núcleos (Intel Xeon, 31 GB de RAM, sin GPU) y USD 0 en llamadas comerciales de IA.

4. **Generalización:** cada tema de práctica corrido como dataset nuevo, sin reajustar (colectivo 30.6, hospital 38.3, litio 51.4). Así encontramos y corregimos que la resolución dependía del tamaño del dataset.
5. **Costo y escala:**
   - USD 0 por cada mil comentarios en llamadas comerciales de IA (el modelo de embeddings corre local); no incluye el costo del hardware;
   - lo más pesado (embeddings) escala con los textos únicos, no con los comentarios;
   - DuckDB resuelve los joins de pares por ventana temporal;
   - para millones de comentarios por día: ingesta incremental en Parquet particionado por día, caché de embeddings por hash de núcleo, grafo de coordinación por ventanas móviles.
6. **Robustez:**
   - un comando;
   - datos sucios: tests con IDs faltantes, fechas inválidas, duplicados, textos vacíos y respuestas a padres inexistentes;
   - semillas y versión del modelo fijadas;
   - corrida desde un clon limpio con salida idéntica byte a byte.
7. **Producto:**
   - NEXO SIGNAL: dashboard React (implementado);
   - ORGANIC LENS: actividad total vs. actividad sin coordinación detectada (implementado);
   - NEXO CONNECT: conexión con APIs oficiales mediante OAuth, sin scraping (no implementado; ver [`INTEGRACIONES.md`](INTEGRACIONES.md)).
8. **Qué existía antes y qué hicimos en el evento:** el material oficial de QualyData (datos, evaluador, línea base) y librerías públicas. Todo `nexo_signal/` y `herramientas/` se desarrolló durante el hackathon.

## Preguntas probables del jurado
- **¿Ajustaron a mano al set de práctica?** No. No hay reglas por tema ni cantidades fijas. Cada tema se validó por separado y la verdad solo se lee en `reporte/diagnostico.py`.
- **¿Es reproducible?** Sí: hay semillas y una revisión del modelo fijadas, y se corrió dos veces desde clones limpios con salida idéntica.
- **¿Cómo distinguen viralidad de coordinación?** La viralidad genuina junta muchas cuentas una sola vez. La coordinación repite coincidencias entre las mismas cuentas, en varias publicaciones, muy por encima del modelo nulo.
- **¿Cuánto cuesta?** USD 0 en llamadas a servicios comerciales de IA: el modelo de embeddings corre localmente en CPU. Ese valor no incluye el costo del hardware ni de la máquina donde se ejecuta.
- **¿Las redes sociales están conectadas?** No. Las plataformas del dashboard se asignan solo para demostrar la interfaz sobre datos sintéticos; NEXO CONNECT y OAuth no están implementados.
