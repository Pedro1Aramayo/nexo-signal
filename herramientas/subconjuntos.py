import argparse
import hashlib
import re
import unicodedata
from pathlib import Path

import pandas as pd


VACIOS = {"", "ninguna", "none", "null"}


def localizar_csv(directorio: Path, nombre: str) -> Path:
    for sufijo in (".csv", ".csv.gz"):
        ruta = directorio / f"{nombre}{sufijo}"
        if ruta.exists():
            return ruta
    raise FileNotFoundError(f"No se encontró {directorio / (nombre + '.csv')} ni su versión .gz")


def leer_csv(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta, dtype=str, keep_default_na=False, compression="infer")


def exigir_columnas(df: pd.DataFrame, columnas: set[str], ruta: Path) -> None:
    faltantes = columnas - set(df.columns)
    if faltantes:
        raise ValueError(f"{ruta} no contiene las columnas requeridas: {sorted(faltantes)}")


def slug_tema(tema: str) -> str:
    texto = unicodedata.normalize("NFKD", tema).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", texto).strip("_").lower()
    return slug or "tema"


def escribir_csv(df: pd.DataFrame, origen: Path, destino: Path) -> None:
    df.to_csv(destino, index=False, compression="gzip" if origen.suffix == ".gz" else None)


def asignar_temas(
    publicaciones: pd.DataFrame,
    comentarios: pd.DataFrame,
    verdad_comentarios: pd.DataFrame,
    verdad_narrativas: pd.DataFrame,
) -> dict[str, str]:
    temas_por_narrativa = {
        narrativa_id.strip(): tema.strip()
        for narrativa_id, tema in zip(
            verdad_narrativas["narrativa_id"], verdad_narrativas["tema"]
        )
    }
    enlaces = verdad_comentarios.merge(
        comentarios[["comentario_id", "publicacion_id"]],
        on="comentario_id",
        how="inner",
    )
    etiquetas = enlaces["narrativa_id"].str.strip().str.lower()
    con_narrativa = enlaces.loc[~etiquetas.isin(VACIOS)].copy()
    publicaciones_con_narrativa = set(con_narrativa["publicacion_id"])
    con_narrativa["tema"] = con_narrativa["narrativa_id"].str.strip().map(
        temas_por_narrativa
    )
    conteos = (
        con_narrativa.dropna(subset=["tema"])
        .groupby(["publicacion_id", "tema"], sort=False)
        .size()
        .rename("cantidad")
        .reset_index()
    )

    temas_por_publicacion = {}
    for publicacion_id, grupo in conteos.groupby("publicacion_id", sort=False):
        maximo = grupo["cantidad"].max()
        ganadores = grupo.loc[grupo["cantidad"].eq(maximo), "tema"]
        if len(ganadores) == 1:
            temas_por_publicacion[publicacion_id] = ganadores.iloc[0]

    temas_por_fuente = {}
    publicaciones_tema = pd.DataFrame(
        temas_por_publicacion.items(), columns=["publicacion_id", "tema"]
    )
    if not publicaciones_tema.empty:
        por_fuente = publicaciones[["publicacion_id", "fuente_id"]].merge(
            publicaciones_tema, on="publicacion_id", how="inner"
        )
        por_fuente = por_fuente.loc[por_fuente["fuente_id"].ne("")]
        conteos_fuente = (
            por_fuente.groupby(["fuente_id", "tema"], sort=False)
            .size()
            .rename("cantidad")
            .reset_index()
        )
        for fuente_id, grupo in conteos_fuente.groupby("fuente_id", sort=False):
            maximo = grupo["cantidad"].max()
            ganadores = grupo.loc[grupo["cantidad"].eq(maximo), "tema"]
            if len(ganadores) == 1:
                temas_por_fuente[fuente_id] = ganadores.iloc[0]

    publicaciones_por_fuente = publicaciones.drop_duplicates("publicacion_id").set_index(
        "publicacion_id"
    )["fuente_id"]
    for publicacion_id in publicaciones["publicacion_id"].drop_duplicates():
        if publicacion_id in temas_por_publicacion or publicacion_id in publicaciones_con_narrativa:
            continue
        fuente_id = publicaciones_por_fuente.get(publicacion_id, "")
        tema = temas_por_fuente.get(fuente_id)
        if tema:
            temas_por_publicacion[publicacion_id] = tema
    return temas_por_publicacion


def crear_subconjuntos(datos: Path, salida: Path) -> list[tuple[str, Path, dict[str, int]]]:
    archivos = {
        "comentarios": localizar_csv(datos, "comentarios"),
        "cuentas": localizar_csv(datos, "cuentas"),
        "publicaciones": localizar_csv(datos, "publicaciones"),
        "fuentes": localizar_csv(datos, "fuentes"),
    }
    verdad = datos / "verdad"
    archivos_verdad = {
        "comentarios": localizar_csv(verdad, "comentarios"),
        "cuentas": localizar_csv(verdad, "cuentas"),
        "narrativas": localizar_csv(verdad, "narrativas"),
        "campanas": localizar_csv(verdad, "campanas"),
    }
    tablas = {nombre: leer_csv(ruta) for nombre, ruta in archivos.items()}
    tablas_verdad = {nombre: leer_csv(ruta) for nombre, ruta in archivos_verdad.items()}

    exigir_columnas(tablas["comentarios"], {"comentario_id", "publicacion_id", "cuenta_id"}, archivos["comentarios"])
    exigir_columnas(tablas["cuentas"], {"cuenta_id"}, archivos["cuentas"])
    exigir_columnas(tablas["publicaciones"], {"publicacion_id", "fuente_id"}, archivos["publicaciones"])
    exigir_columnas(tablas["fuentes"], {"fuente_id"}, archivos["fuentes"])
    exigir_columnas(tablas_verdad["comentarios"], {"comentario_id", "narrativa_id"}, archivos_verdad["comentarios"])
    exigir_columnas(tablas_verdad["cuentas"], {"cuenta_id", "campana_id"}, archivos_verdad["cuentas"])
    exigir_columnas(tablas_verdad["narrativas"], {"narrativa_id", "tema"}, archivos_verdad["narrativas"])
    exigir_columnas(tablas_verdad["campanas"], {"campana_id"}, archivos_verdad["campanas"])

    temas = sorted(tablas_verdad["narrativas"]["tema"].drop_duplicates())
    if not temas or any(not tema for tema in temas):
        raise ValueError(f"{archivos_verdad['narrativas']} debe contener temas no vacíos")
    nombres_usados = {}
    temas_por_publicacion = asignar_temas(
        tablas["publicaciones"],
        tablas["comentarios"],
        tablas_verdad["comentarios"],
        tablas_verdad["narrativas"],
    )
    resultado = []
    for tema in temas:
        slug = slug_tema(tema)
        if slug in nombres_usados and nombres_usados[slug] != tema:
            slug = f"{slug}-{hashlib.sha1(tema.encode('utf-8')).hexdigest()[:8]}"
        nombres_usados[slug] = tema
        directorio = salida / f"sub_{slug}"
        verdad_salida = directorio / "verdad"
        verdad_salida.mkdir(parents=True, exist_ok=True)

        ids_publicacion = {
            publicacion_id
            for publicacion_id, tema_publicacion in temas_por_publicacion.items()
            if tema_publicacion == tema
        }
        sub_publicaciones = tablas["publicaciones"].loc[
            tablas["publicaciones"]["publicacion_id"].isin(ids_publicacion)
        ]
        sub_comentarios = tablas["comentarios"].loc[
            tablas["comentarios"]["publicacion_id"].isin(ids_publicacion)
        ]
        ids_comentario = set(sub_comentarios["comentario_id"])
        ids_cuenta = set(sub_comentarios["cuenta_id"])
        ids_fuente = set(sub_publicaciones["fuente_id"])
        sub_cuentas = tablas["cuentas"].loc[tablas["cuentas"]["cuenta_id"].isin(ids_cuenta)]
        sub_fuentes = tablas["fuentes"].loc[tablas["fuentes"]["fuente_id"].isin(ids_fuente)]

        sub_verdad_comentarios = tablas_verdad["comentarios"].loc[
            tablas_verdad["comentarios"]["comentario_id"].isin(ids_comentario)
        ]
        sub_verdad_cuentas = tablas_verdad["cuentas"].loc[
            tablas_verdad["cuentas"]["cuenta_id"].isin(ids_cuenta)
        ]
        ids_campana = {
            campana_id
            for campana_id in sub_verdad_cuentas["campana_id"]
            if campana_id.strip().lower() not in VACIOS
        }
        sub_verdad_narrativas = tablas_verdad["narrativas"].loc[
            tablas_verdad["narrativas"]["tema"].eq(tema)
        ]
        sub_verdad_campanas = tablas_verdad["campanas"].loc[
            tablas_verdad["campanas"]["campana_id"].isin(ids_campana)
        ]

        for nombre, df in (
            ("comentarios", sub_comentarios),
            ("cuentas", sub_cuentas),
            ("publicaciones", sub_publicaciones),
            ("fuentes", sub_fuentes),
        ):
            escribir_csv(df, archivos[nombre], directorio / archivos[nombre].name)
        for nombre, df in (
            ("comentarios", sub_verdad_comentarios),
            ("cuentas", sub_verdad_cuentas),
            ("narrativas", sub_verdad_narrativas),
            ("campanas", sub_verdad_campanas),
        ):
            escribir_csv(df, archivos_verdad[nombre], verdad_salida / archivos_verdad[nombre].name)

        resultado.append(
            (
                tema,
                directorio,
                {
                    "comentarios": len(sub_comentarios),
                    "publicaciones": len(sub_publicaciones),
                    "cuentas": len(sub_cuentas),
                    "narrativas": len(sub_verdad_narrativas),
                },
            )
        )
    return resultado


def main() -> None:
    ap = argparse.ArgumentParser(description="Construye subconjuntos de práctica por tema.")
    ap.add_argument("--datos", type=Path, default=Path("datos/practica"))
    ap.add_argument("--salida", type=Path, default=Path("salida"))
    args = ap.parse_args()
    for tema, directorio, conteos in crear_subconjuntos(args.datos, args.salida):
        print(
            f"{tema}: {directorio} "
            f"(comentarios={conteos['comentarios']}, publicaciones={conteos['publicaciones']}, "
            f"cuentas={conteos['cuentas']}, narrativas={conteos['narrativas']})"
        )


if __name__ == "__main__":
    main()
