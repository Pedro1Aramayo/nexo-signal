from pathlib import Path

import duckdb
import pandas as pd


ARCHIVOS = {
    "fuentes": "fuentes.csv",
    "publicaciones": "publicaciones.csv",
    "comentarios": "comentarios.csv",
    "cuentas": "cuentas.csv",
}


def _leer_csv(ruta: Path) -> pd.DataFrame:
    conexion = duckdb.connect()
    try:
        return conexion.execute(
            "SELECT * FROM read_csv_auto(?, header=true, all_varchar=true, "
            "null_padding=true, ignore_errors=true)",
            [str(ruta)],
        ).fetchdf()
    finally:
        conexion.close()


def cargar(datos: Path, cache: Path) -> dict[str, pd.DataFrame]:
    """Carga, limpia y guarda las cuatro tablas en Parquet."""
    tablas = {}
    for tabla, nombre in ARCHIVOS.items():
        ruta = datos / nombre
        if not ruta.exists() and ruta.with_suffix(ruta.suffix + ".gz").exists():
            ruta = ruta.with_suffix(ruta.suffix + ".gz")
        if not ruta.exists():
            raise FileNotFoundError(f"No se encontró {datos / nombre} ni su versión gzip")
        df = _leer_csv(ruta)
        for columna in df.columns:
            df[columna] = df[columna].map(
                lambda valor: valor.strip() if isinstance(valor, str) else valor
            )
        tablas[tabla] = df

    comentarios = tablas["comentarios"]
    for columna in ("comentario_id", "cuenta_id", "texto", "respuesta_a", "fecha"):
        if columna not in comentarios:
            comentarios[columna] = ""
    comentarios = comentarios[
        comentarios["comentario_id"].fillna("").ne("")
        & comentarios["cuenta_id"].fillna("").ne("")
    ].copy()
    comentarios["texto"] = comentarios["texto"].fillna("")
    comentarios["respuesta_a"] = comentarios["respuesta_a"].fillna("")
    comentarios = comentarios.drop_duplicates("comentario_id", keep="first").reset_index(drop=True)
    comentarios["fecha_dt"] = pd.to_datetime(comentarios["fecha"], errors="coerce", utc=True)
    ids = set(comentarios["comentario_id"])
    comentarios.loc[~comentarios["respuesta_a"].isin(ids), "respuesta_a"] = ""
    tablas["comentarios"] = comentarios

    cuentas = tablas["cuentas"]
    if "cuenta_id" not in cuentas:
        cuentas["cuenta_id"] = ""
    cuentas = cuentas[cuentas["cuenta_id"].fillna("").ne("")].drop_duplicates(
        "cuenta_id", keep="first"
    ).reset_index(drop=True)
    tablas["cuentas"] = cuentas

    cache.mkdir(parents=True, exist_ok=True)
    for nombre, df in tablas.items():
        df.to_parquet(cache / f"{nombre}.parquet", index=False)
    return tablas
