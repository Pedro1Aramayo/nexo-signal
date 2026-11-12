import csv
import gzip
from pathlib import Path

import duckdb
import pandas as pd


ARCHIVOS = {
    "fuentes": "fuentes.csv",
    "publicaciones": "publicaciones.csv",
    "comentarios": "comentarios.csv",
    "cuentas": "cuentas.csv",
}
ORDEN_ENTRADA = "__nexo_orden_entrada"
RECUPERADO = "__nexo_recuperado"
COLUMNAS = {
    "fuentes": ("fuente_id", "nombre", "tipo"),
    "publicaciones": ("publicacion_id", "fuente_id", "fecha", "titular"),
    "comentarios": (
        "comentario_id", "publicacion_id", "cuenta_id", "fecha",
        "texto", "respuesta_a", "me_gusta",
    ),
    "cuentas": (
        "cuenta_id", "usuario", "fecha_creacion", "seguidores", "siguiendo",
    ),
}


def _leer_encabezado(ruta: Path) -> list[str]:
    abrir = gzip.open if ruta.suffix == ".gz" else open
    with abrir(ruta, "rt", encoding="utf-8-sig", newline="") as archivo:
        encabezado = next(csv.reader(archivo), [])
    return [nombre.strip().lstrip("\ufeff").strip() for nombre in encabezado]


def _leer_csv(
    ruta: Path, tabla: str
) -> tuple[pd.DataFrame, pd.DataFrame, list[str], bool]:
    encabezado = _leer_encabezado(ruta)
    esquema_alternativo = encabezado != list(COLUMNAS[tabla])
    columnas_sql = "{" + ", ".join(
        f"'{columna}':'VARCHAR'" for columna in COLUMNAS[tabla]
    ) + "}"
    conexion = duckdb.connect()
    try:
        if esquema_alternativo:
            datos = conexion.execute(
                "SELECT * FROM read_csv_auto(?, header=true, all_varchar=true, "
                "null_padding=true, ignore_errors=true, store_rejects=true, "
                "strict_mode=true, rejects_table='nexo_rechazos', "
                "rejects_scan='nexo_escaneos') WITH ORDINALITY",
                [str(ruta)],
            ).fetchdf()
            columnas = [
                columna
                if columna == "ordinality"
                else str(columna).strip().lstrip("\ufeff").strip()
                for columna in datos.columns
            ]
            datos.columns = columnas
            datos = datos.rename(columns={"ordinality": ORDEN_ENTRADA})
            for columna in COLUMNAS[tabla]:
                if columna not in datos:
                    datos[columna] = ""
        else:
            datos = conexion.execute(
                "SELECT * FROM read_csv(?, auto_detect=false, header=true, delim=',', "
                "quote='\"', escape='\"', all_varchar=true, null_padding=true, "
                "ignore_errors=true, store_rejects=true, strict_mode=true, "
                "rejects_table='nexo_rechazos', rejects_scan='nexo_escaneos', "
                f"columns={columnas_sql}) WITH ORDINALITY",
                [str(ruta)],
            ).fetchdf().rename(columns={"ordinality": ORDEN_ENTRADA})
        try:
            rechazos = conexion.execute(
                "SELECT line, csv_line FROM nexo_rechazos ORDER BY line"
            ).fetchdf()
        except duckdb.CatalogException:
            rechazos = pd.DataFrame(columns=["line", "csv_line"])
        return datos, rechazos, encabezado, esquema_alternativo
    finally:
        conexion.close()


def _campo(fila_csv: str, indice: int) -> str:
    try:
        campos = next(csv.reader([fila_csv], strict=False))
    except csv.Error:
        campos = fila_csv.split(",")
    if indice < 0 or indice >= len(campos):
        return ""
    campo = campos[indice]
    return campo.strip().lstrip("\ufeff")


def _recuperar_rechazos(
    comentarios: pd.DataFrame,
    rechazos: pd.DataFrame,
    indice_comentario_id: int | None,
) -> tuple[pd.DataFrame, int]:
    rechazos = rechazos.drop_duplicates("line", keep="first")
    posiciones = sorted(max(1, int(linea) - 1) for linea in rechazos["line"])

    def ajustar_orden(ordinal: int) -> int:
        posicion = int(ordinal)
        for rechazo in posiciones:
            if rechazo <= posicion:
                posicion += 1
        return posicion

    comentarios[ORDEN_ENTRADA] = comentarios[ORDEN_ENTRADA].map(ajustar_orden)
    comentarios[RECUPERADO] = False
    ids_existentes = {
        str(valor).strip()
        for valor in comentarios["comentario_id"]
        if pd.notna(valor) and str(valor).strip()
    }
    recuperados = []
    for rechazo in rechazos.itertuples(index=False):
        if indice_comentario_id is None or pd.isna(rechazo.csv_line):
            continue
        comentario_id = _campo(str(rechazo.csv_line), indice_comentario_id)
        if not comentario_id or comentario_id in ids_existentes:
            continue
        fila = dict.fromkeys(COLUMNAS["comentarios"], "")
        fila["comentario_id"] = comentario_id
        fila[ORDEN_ENTRADA] = max(1, int(rechazo.line) - 1)
        fila[RECUPERADO] = True
        recuperados.append(fila)
        ids_existentes.add(comentario_id)
    if recuperados:
        comentarios = pd.concat(
            [comentarios, pd.DataFrame(recuperados)], ignore_index=True
        )
    return (
        comentarios.sort_values(ORDEN_ENTRADA, kind="stable").reset_index(drop=True),
        len(recuperados),
    )


def cargar(datos: Path, cache: Path) -> dict[str, pd.DataFrame]:
    """Carga, limpia y guarda las cuatro tablas en Parquet."""
    tablas = {}
    estadisticas_comentarios = {}
    esquemas_alternativos = []
    for tabla, nombre in ARCHIVOS.items():
        ruta = datos / nombre
        if not ruta.exists() and ruta.with_suffix(ruta.suffix + ".gz").exists():
            ruta = ruta.with_suffix(ruta.suffix + ".gz")
        if not ruta.exists():
            raise FileNotFoundError(f"No se encontró {datos / nombre} ni su versión gzip")
        df, rechazos, encabezado, esquema_alternativo = _leer_csv(ruta, tabla)
        if esquema_alternativo:
            esquemas_alternativos.append(tabla)
        if tabla == "comentarios":
            filas_entrada = len(df) + rechazos["line"].nunique()
            indice_comentario_id = (
                encabezado.index("comentario_id")
                if "comentario_id" in encabezado
                else None
            )
            df, filas_recuperadas = _recuperar_rechazos(
                df, rechazos, indice_comentario_id
            )
            estadisticas_comentarios = {
                "filas_entrada": int(filas_entrada),
                "comentarios_rechazados": int(rechazos["line"].nunique()),
                "comentarios_recuperados": int(filas_recuperadas),
                "esquema_alternativo": esquemas_alternativos,
            }
        for columna in df.columns:
            df[columna] = df[columna].map(
                lambda valor: valor.strip() if isinstance(valor, str) else valor
            )
        tablas[tabla] = df

    comentarios = tablas["comentarios"]
    for columna in ("comentario_id", "cuenta_id", "texto", "respuesta_a", "fecha"):
        if columna not in comentarios:
            comentarios[columna] = ""
    if RECUPERADO not in comentarios:
        comentarios[RECUPERADO] = False
    comentarios = comentarios[
        comentarios["comentario_id"].fillna("").ne("")
        & (comentarios["cuenta_id"].fillna("").ne("") | comentarios[RECUPERADO])
    ].copy()
    comentarios["texto"] = comentarios["texto"].fillna("")
    comentarios["respuesta_a"] = comentarios["respuesta_a"].fillna("")
    comentarios = comentarios.drop_duplicates("comentario_id", keep="first").reset_index(drop=True)
    comentarios["fecha_dt"] = pd.to_datetime(comentarios["fecha"], errors="coerce", utc=True)
    ids = set(comentarios["comentario_id"])
    comentarios.loc[~comentarios["respuesta_a"].isin(ids), "respuesta_a"] = ""
    comentarios.attrs["ingesta"] = estadisticas_comentarios
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
