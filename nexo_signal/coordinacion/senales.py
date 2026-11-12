import time

import duckdb
import pandas as pd


def calcular_senales(comentarios: pd.DataFrame) -> tuple[dict, dict[str, float]]:
    conexion = duckdb.connect()
    tiempos = {}
    try:
        columnas = comentarios[[
            "comentario_id", "publicacion_id", "cuenta_id",
            "fecha_dt", "respuesta_a", "core",
        ]]
        conexion.register("entrada", columnas)
        conexion.execute(
            """
            CREATE TEMP TABLE comentarios AS
            SELECT comentario_id, publicacion_id, cuenta_id,
                   CAST(epoch(fecha_dt) AS BIGINT) AS ts, respuesta_a, core
            FROM entrada
            WHERE fecha_dt IS NOT NULL AND cuenta_id <> ''
            """
        )
        inicio = time.perf_counter()
        ec = conexion.execute(
            """
            SELECT x.cuenta_id AS a, y.cuenta_id AS b,
                   COUNT(DISTINCT x.publicacion_id)::BIGINT AS k
            FROM comentarios x
            JOIN comentarios y
              ON x.publicacion_id = y.publicacion_id
             AND x.cuenta_id < y.cuenta_id
             AND abs(x.ts - y.ts) <= 600
            GROUP BY a, b
            HAVING COUNT(DISTINCT x.publicacion_id) >= 2
            """
        ).fetchdf()
        tiempos["ec"] = round(time.perf_counter() - inicio, 3)

        inicio = time.perf_counter()
        ed = conexion.execute(
            """
            SELECT x.cuenta_id AS a, y.cuenta_id AS b, COUNT(*)::BIGINT AS k
            FROM comentarios x
            JOIN comentarios y
              ON x.core = y.core
             AND x.cuenta_id < y.cuenta_id
             AND abs(x.ts - y.ts) <= 7200
            WHERE length(x.core) >= 25
            GROUP BY a, b
            """
        ).fetchdf()
        tiempos["ed"] = round(time.perf_counter() - inicio, 3)

        inicio = time.perf_counter()
        er = conexion.execute(
            """
            SELECT least(x.cuenta_id, p.cuenta_id) AS a,
                   greatest(x.cuenta_id, p.cuenta_id) AS b,
                   COUNT(*)::BIGINT AS k
            FROM comentarios x
            JOIN comentarios p ON x.respuesta_a = p.comentario_id
            WHERE x.respuesta_a <> '' AND x.cuenta_id <> p.cuenta_id
            GROUP BY a, b
            """
        ).fetchdf()
        tiempos["er"] = round(time.perf_counter() - inicio, 3)
        return {"ec": ec, "ed": ed, "er": er}, tiempos
    finally:
        conexion.close()
