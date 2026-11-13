# NEXO SIGNAL — material para video y pitch (Hacki)

## Mensaje central (1 frase)
NEXO SIGNAL lee cientos de miles de comentarios en aproximadamente 65 segundos, en una notebook y sin pagar IA. Encuentra qué se está diciendo, quién apoya y quién rechaza, cuándo empezó cada narrativa y qué parte de la conversación está fabricada por operaciones coordinadas.

## Guion del video (≈ 3 min)
1. **Problema (20 s).** En una conversación pública, 200.000 comentarios no se pueden leer, y la IA comentario por comentario es lenta y cara. Las operaciones coordinadas no se ven mirando un comentario: aparecen solo en el conjunto.
2. **Demo: un comando (20 s).** Terminal con `make entrega`: se ve que termina en ~1 minuto y que `costo.json` marca USD 0.
3. **Demo: narrativas (60 s).** Abrir la demo HTML (`make demo`) y mostrar:
   - los KPIs;
   - una narrativa estable;
   - una narrativa emergente, con la marca de origen sobre la curva diaria;
   - la barra apoya/rechaza;
   - los comentarios representativos de cada lado.
4. **Demo: coordinación (40 s).** En la tabla de operaciones, mostrar tres estilos distintos:
   - sincronía y texto repetido;
   - cuentas recién creadas que comentan de noche;
   - una red de respuestas entre cuentas antiguas, que es la difícil.
   
   Explicar que cada grupo es varias veces más denso de lo que produciría el azar, y que así se descarta la viralidad genuina.
5. **ORGANIC LENS (20 s).** Qué porcentaje del volumen de cada narrativa está inflado por cuentas coordinadas.
6. **Cierre (20 s).** Mostrar:
   - el puntaje en práctica: línea base 21.96 → NEXO 51.65 / 55;
   - la prueba de generalización, un tema por vez sin reajustar;
   - el camino a SaaS con NEXO CONNECT (Instagram oficial).

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
   | USD IA | 0 | 0 |

   **Set final (sin verdad, 150.000 comentarios):** 12 narrativas, 19,5% de ruido, 3 operaciones coordinadas (94 cuentas: 52 con texto repetido sincronizado, 21 de cuentas antiguas en red de respuestas, 21 nocturnas en una sola publicación), 65 s en CPU, USD 0.

4. **Generalización:** cada tema de práctica corrido como dataset nuevo, sin reajustar (colectivo 30.6, hospital 38.3, litio 51.4). Así encontramos y corregimos que la resolución dependía del tamaño del dataset.
5. **Costo y escala:**
   - el costo es USD 0 por cada mil comentarios;
   - lo más pesado (embeddings) escala con los textos únicos, no con los comentarios;
   - DuckDB resuelve los joins de pares por ventana temporal;
   - para millones de comentarios por día: ingesta incremental en Parquet particionado por día, caché de embeddings por hash de núcleo, grafo de coordinación por ventanas móviles.
6. **Robustez:**
   - un comando;
   - datos sucios: tests con IDs faltantes, fechas inválidas, duplicados, textos vacíos y respuestas a padres inexistentes;
   - semillas y versión del modelo fijadas;
   - corrida desde un clon limpio con salida idéntica byte a byte.
7. **Producto:**
   - NEXO SIGNAL: dashboard;
   - ORGANIC LENS: volumen orgánico vs. inflado;
   - NEXO CONNECT: Instagram Graph API con OAuth, sin scraping.
8. **Qué existía antes y qué hicimos en el evento:** el material oficial de QualyData (datos, evaluador, línea base) y librerías públicas. Todo `nexo_signal/` y `herramientas/` se desarrolló durante el hackathon.

## Preguntas probables del jurado
- **¿Ajustaron a mano al set de práctica?** No. No hay reglas por tema ni cantidades fijas. Cada tema se validó por separado y la verdad solo se lee en `reporte/diagnostico.py`.
- **¿Es reproducible?** Sí: hay semillas y una revisión del modelo fijadas, y se corrió dos veces desde clones limpios con salida idéntica.
- **¿Cómo distinguen viralidad de coordinación?** La viralidad genuina junta muchas cuentas una sola vez. La coordinación repite coincidencias entre las mismas cuentas, en varias publicaciones, muy por encima del modelo nulo.
