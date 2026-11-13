import argparse
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd


PLATAFORMAS_DEMO = ("instagram", "facebook", "x", "youtube", "tiktok")
CATEGORIAS = ("sugerencia", "queja", "consulta", "elogio", "otro")
NOMBRES_DATASET = {
    "practica": "Set de práctica QualyData (sintético)",
    "final": "Set final QualyData (sintético)",
}
SUGERENCIA_FUERTE = (
    "por que no", "deberian", "deberia", "habria que", "propongo", "sugiero",
    "tendrian que", "estaria bueno",
)
SUGERENCIA = (
    "hay que", "hay q", "pongan", "hagan", "controlen", "arreglen",
    "que muestren", "necesitamos", "ojala", "primero",
)
QUEJA = (
    "verguenza", "nadie", "siempre lo mismo", "robo", "roban", "chorros",
    "mentira", "mienten", "basta", "harto", "harta", "indignante",
    "desastre", "abandono", "no puede ser", "burla", "estafa", "otra vez",
    "como siempre", "nunca", "inutiles", "corruptos", "se llevaron", "peor",
    "bronca", "lamentable", "triste", "falta de respeto", "a pedazos",
    "no hay", "tardan", "abandonados", "se muere",
)
ELOGIO = (
    "gracias", "excelente", "genial", "muy bien", "buenisimo",
    "felicitaciones", "bravo", "orgullo", "me encanta", "que lindo",
    "bien ahi", "aplausos", "buena noticia", "bien hecho", "por fin",
    "mejoro", "avanza", "me atendieron", "buen trabajo",
)
PATRONES = {
    nombre: tuple(
        re.compile(r"\b" + re.escape(frase) + r"\b")
        for frase in frases
    )
    for nombre, frases in (
        ("sugerencia_fuerte", SUGERENCIA_FUERTE),
        ("sugerencia", SUGERENCIA),
        ("queja", QUEJA),
        ("elogio", ELOGIO),
    )
}
COLUMNAS_NUMERICAS_GRUPO = {
    "n_cuentas",
    "densidad",
    "ratio",
    "mediana_dias_cuenta_al_primer_comentario",
    "mediana_seguidores",
    "frac_nocturna",
    "n_publicaciones",
}


def _sin_acentos(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", str(texto).lower())
    return "".join(
        caracter
        for caracter in descompuesto
        if not unicodedata.combining(caracter)
    )


def categoria(texto: str) -> str:
    normalizado = _sin_acentos(texto or "").strip()
    if any(patron.search(normalizado) for patron in PATRONES["sugerencia_fuerte"]):
        return "sugerencia"
    if "?" in normalizado or "¿" in normalizado:
        return (
            "queja"
            if any(patron.search(normalizado) for patron in PATRONES["queja"])
            else "consulta"
        )
    if any(patron.search(normalizado) for patron in PATRONES["sugerencia"]):
        return "sugerencia"
    if any(patron.search(normalizado) for patron in PATRONES["queja"]):
        return "queja"
    if any(patron.search(normalizado) for patron in PATRONES["elogio"]):
        return "elogio"
    return "otro"


def _leer_tabla(datos: Path, nombre: str) -> pd.DataFrame:
    ruta = datos / nombre
    if not ruta.exists():
        ruta = datos / f"{nombre}.gz"
    return pd.read_csv(ruta, dtype=str, keep_default_na=False)


def _numero_o_nulo(valor):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numero):
        return None
    return int(numero) if numero.is_integer() else numero


def _entero(valor) -> int:
    numero = _numero_o_nulo(valor)
    return int(numero) if numero is not None else 0


def _normalizar_narrativa(valor: str) -> str:
    valor = str(valor or "").strip()
    return "ninguna" if not valor or valor.casefold() == "ninguna" else valor


def _ordenar_cuentas(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.drop_duplicates("cuenta_id", keep="first")


def _conteo_categorias(frame: pd.DataFrame) -> dict[str, int]:
    conteos = Counter(frame["categoria"].tolist())
    return {nombre: int(conteos[nombre]) for nombre in CATEGORIAS}


def _ordenar_conteos(conteos: Counter, limite: int):
    return sorted(conteos.items(), key=lambda item: (-item[1], item[0]))[:limite]


def _escribir_json(ruta: Path, contenido) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(
            contenido,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )


def _top_narrativas(frame: pd.DataFrame, titulos: dict[str, str], limite: int):
    narrativas = frame[frame["_narrativa"] != "ninguna"]
    conteos = Counter(narrativas["_narrativa"].tolist())
    resultado = []
    for nombre, cantidad in _ordenar_conteos(conteos, limite):
        grupo = narrativas[narrativas["_narrativa"] == nombre]
        resultado.append({
            "narrativa": nombre,
            "titulo": titulos.get(nombre, ""),
            "n": int(cantidad),
            "apoya": int((grupo["postura"] == "apoya").sum()),
            "rechaza": int((grupo["postura"] == "rechaza").sum()),
        })
    return resultado


def _top_publicaciones(
    frame: pd.DataFrame, publicaciones: dict[str, dict], limite: int
):
    conteos = Counter(frame["publicacion_id"].tolist())
    return [
        {
            "publicacion_id": publicacion_id,
            "titular": publicaciones.get(publicacion_id, {}).get("titular", ""),
            "n": int(cantidad),
        }
        for publicacion_id, cantidad in _ordenar_conteos(conteos, limite)
    ]


def _comentario_exportable(fila: dict) -> dict:
    narrativa = fila["_narrativa"]
    ruido = narrativa == "ninguna"
    return {
        "id": fila["comentario_id"],
        "cuenta_id": fila["cuenta_id"],
        "usuario": fila["usuario"],
        "fecha": fila["fecha"],
        "texto": fila["texto"],
        "respuesta_a": fila["respuesta_a"],
        "me_gusta": int(fila["_me_gusta"]),
        "narrativa": None if ruido else narrativa,
        "postura": None if ruido or not fila["postura"] else fila["postura"],
        "categoria": fila["categoria"],
        "grupo": fila["grupo"] or None,
    }


def exportar(
    datos: Path,
    entrega: Path,
    salida: Path,
    conjunto: str = "practica",
) -> None:
    fuentes = _leer_tabla(datos, "fuentes.csv").drop_duplicates(
        "fuente_id", keep="first"
    )
    publicaciones = _leer_tabla(datos, "publicaciones.csv").drop_duplicates(
        "publicacion_id", keep="first"
    )
    comentarios_raw = _leer_tabla(datos, "comentarios.csv")
    comentarios_raw = comentarios_raw[
        comentarios_raw["comentario_id"].ne("")
    ].drop_duplicates("comentario_id", keep="first")
    cuentas_raw = _ordenar_cuentas(_leer_tabla(datos, "cuentas.csv"))

    comentarios_motor = pd.read_csv(
        entrega / "comentarios.csv", dtype=str, keep_default_na=False
    ).drop_duplicates("comentario_id", keep="first")
    narrativas_motor = pd.read_csv(
        entrega / "narrativas.csv", dtype=str, keep_default_na=False
    ).drop_duplicates("narrativa", keep="first")
    cuentas_motor = _ordenar_cuentas(pd.read_csv(
        entrega / "cuentas.csv", dtype=str, keep_default_na=False
    ))
    costo = json.loads((entrega / "costo.json").read_text(encoding="utf-8"))
    grupos_evidencia = pd.read_csv(
        entrega / "evidencia" / "grupos_coordinados.csv",
        dtype=str,
        keep_default_na=False,
    )

    plataformas = {
        fuente_id: PLATAFORMAS_DEMO[indice % len(PLATAFORMAS_DEMO)]
        for indice, fuente_id in enumerate(sorted(fuentes["fuente_id"].tolist()))
    }
    fuentes["plataforma_demo"] = fuentes["fuente_id"].map(plataformas)
    fuentes = fuentes.fillna("")

    comentarios = comentarios_raw.merge(
        comentarios_motor[["comentario_id", "narrativa", "postura"]],
        on="comentario_id",
        how="left",
    )
    comentarios = comentarios.merge(
        cuentas_motor[["cuenta_id", "grupo"]],
        on="cuenta_id",
        how="left",
    )
    comentarios = comentarios.merge(
        cuentas_raw[["cuenta_id", "usuario"]],
        on="cuenta_id",
        how="left",
    )
    comentarios[["narrativa", "postura", "grupo", "usuario"]] = (
        comentarios[["narrativa", "postura", "grupo", "usuario"]].fillna("")
    )
    comentarios["_narrativa"] = comentarios["narrativa"].map(
        _normalizar_narrativa
    )
    comentarios["_coordinado"] = comentarios["grupo"].ne("")
    comentarios["categoria"] = comentarios["texto"].map(categoria)
    comentarios["_me_gusta"] = (
        pd.to_numeric(comentarios["me_gusta"], errors="coerce")
        .fillna(0)
        .astype(int)
    )
    comentarios["_fecha_ts"] = pd.to_datetime(
        comentarios["fecha"], utc=True, errors="coerce"
    )
    comentarios["_dia"] = (
        comentarios["_fecha_ts"].dt.tz_convert("-03:00").dt.strftime("%Y-%m-%d")
    ).fillna("")
    comentarios["fuente_id"] = comentarios["publicacion_id"].map(
        publicaciones.set_index("publicacion_id")["fuente_id"]
    ).fillna("")
    comentarios = comentarios.sort_values(
        ["_fecha_ts", "comentario_id"],
        ascending=[True, True],
        kind="stable",
        na_position="last",
    ).reset_index(drop=True)

    titulos = dict(zip(narrativas_motor["narrativa"], narrativas_motor["titulo"]))
    narrativas_motor = narrativas_motor.set_index("narrativa", drop=False)
    publicaciones_info = publicaciones.merge(
        fuentes[["fuente_id", "nombre", "tipo", "plataforma_demo"]],
        on="fuente_id",
        how="left",
        suffixes=("", "_fuente"),
    ).fillna("")
    publicaciones_info["_fecha_ts"] = pd.to_datetime(
        publicaciones_info["fecha"], utc=True, errors="coerce"
    )
    publicaciones_info = publicaciones_info.sort_values(
        ["_fecha_ts", "publicacion_id"],
        ascending=[False, True],
        kind="stable",
        na_position="last",
    ).reset_index(drop=True)
    publicaciones_lookup = {
        fila["publicacion_id"]: fila
        for fila in publicaciones_info.to_dict(orient="records")
    }
    comentarios_por_publicacion = {
        nombre: grupo
        for nombre, grupo in comentarios.groupby("publicacion_id", sort=False)
    }

    fuentes_publicaciones = Counter(publicaciones["fuente_id"].tolist())
    fuentes_comentarios = Counter(comentarios["fuente_id"].tolist())
    fuentes_json = [
        {
            "fuente_id": fila["fuente_id"],
            "nombre": fila["nombre"],
            "tipo": fila["tipo"],
            "plataforma_demo": fila["plataforma_demo"],
            "publicaciones": int(fuentes_publicaciones[fila["fuente_id"]]),
            "comentarios": int(fuentes_comentarios[fila["fuente_id"]]),
        }
        for fila in fuentes.sort_values("fuente_id", kind="stable").to_dict(
            orient="records"
        )
    ]

    publicaciones_json = []
    for fila in publicaciones_info.to_dict(orient="records"):
        grupo = comentarios_por_publicacion.get(
            fila["publicacion_id"], comentarios.iloc[0:0]
        )
        publicaciones_json.append({
            "publicacion_id": fila["publicacion_id"],
            "fuente_id": fila["fuente_id"],
            "fuente_nombre": fila["nombre"],
            "fuente_tipo": fila["tipo"],
            "plataforma_demo": fila["plataforma_demo"],
            "fecha": fila["fecha"],
            "titular": fila["titular"],
            "comentarios": int(len(grupo)),
            "coordinados": int(grupo["_coordinado"].sum()),
            "ruido": int((grupo["_narrativa"] == "ninguna").sum()),
            "me_gusta_total": int(grupo["_me_gusta"].sum()),
            "categorias": _conteo_categorias(grupo),
            "narrativas": _top_narrativas(grupo, titulos, 5),
        })

    narrativas_json = []
    for nombre in sorted(narrativas_motor.index.tolist()):
        fila = narrativas_motor.loc[nombre]
        grupo = comentarios[comentarios["_narrativa"] == nombre]
        serie = []
        por_dia = grupo[grupo["_dia"] != ""].groupby("_dia", sort=True)
        for dia, comentarios_dia in por_dia:
            serie.append({
                "dia": dia,
                "total": int(len(comentarios_dia)),
                "organico": int((~comentarios_dia["_coordinado"]).sum()),
            })
        frases = [
            frase
            for frase in fila["frases_clave"].split("|")
            if frase
        ]
        narrativas_json.append({
            "narrativa": nombre,
            "titulo": fila["titulo"],
            "frases_clave": frases,
            "fecha_origen": fila["fecha_origen"],
            "total": int(len(grupo)),
            "apoya": int((grupo["postura"] == "apoya").sum()),
            "rechaza": int((grupo["postura"] == "rechaza").sum()),
            "organico_total": int((~grupo["_coordinado"]).sum()),
            "coordinados": int(grupo["_coordinado"].sum()),
            "serie": serie,
            "publicaciones_top": _top_publicaciones(
                grupo, publicaciones_lookup, 5
            ),
        })

    cuentas_por_id = cuentas_raw.set_index("cuenta_id").to_dict(orient="index")
    coordinacion_json = []
    for fila in grupos_evidencia.sort_values("grupo", kind="stable").to_dict(
        orient="records"
    ):
        nombre = fila["grupo"]
        grupo_comentarios = comentarios[comentarios["grupo"] == nombre]
        ids_cuentas = sorted(grupo_comentarios["cuenta_id"].drop_duplicates())
        cuentas_grupo = [
            {
                "cuenta_id": cuenta_id,
                "usuario": cuentas_por_id.get(cuenta_id, {}).get("usuario", ""),
                "fecha_creacion": cuentas_por_id.get(cuenta_id, {}).get(
                    "fecha_creacion", ""
                ),
                "seguidores": _numero_o_nulo(
                    cuentas_por_id.get(cuenta_id, {}).get("seguidores", "")
                ),
            }
            for cuenta_id in ids_cuentas
        ]
        narrativas_grupo = Counter(
            grupo_comentarios.loc[
                grupo_comentarios["_narrativa"] != "ninguna", "_narrativa"
            ].tolist()
        )
        fila_exportada = {
            clave: (
                _numero_o_nulo(valor)
                if clave in COLUMNAS_NUMERICAS_GRUPO
                else valor
            )
            for clave, valor in fila.items()
        }
        textos = [
            texto
            for texto in grupo_comentarios["texto"].tolist()
            if texto.strip()
        ]
        ejemplos = [
            texto
            for texto, _ in _ordenar_conteos(Counter(textos), 5)
        ]
        fila_exportada.update({
            "cuentas": cuentas_grupo,
            "comentarios": int(len(grupo_comentarios)),
            "narrativas": [
                {"narrativa": etiqueta, "n": int(cantidad)}
                for etiqueta, cantidad in _ordenar_conteos(narrativas_grupo, 3)
            ],
            "publicaciones_top": _top_publicaciones(
                grupo_comentarios, publicaciones_lookup, 5
            ),
            "ejemplos": ejemplos,
        })
        coordinacion_json.append(fila_exportada)

    fechas_validas = comentarios[comentarios["_fecha_ts"].notna()].sort_values(
        "_fecha_ts", kind="stable"
    )
    fecha_min = fechas_validas.iloc[0]["fecha"] if len(fechas_validas) else ""
    fecha_max = fechas_validas.iloc[-1]["fecha"] if len(fechas_validas) else ""
    cuentas_coordinadas = cuentas_motor["grupo"].ne("")
    narrativas_asignadas = set(
        comentarios.loc[
            comentarios["_narrativa"] != "ninguna", "_narrativa"
        ].tolist()
    )
    resumen = {
        "conjunto": conjunto,
        "dataset": NOMBRES_DATASET[conjunto],
        "comentarios": int(len(comentarios)),
        "publicaciones": int(len(publicaciones)),
        "fuentes": int(len(fuentes)),
        "cuentas": int(len(cuentas_raw)),
        "narrativas": int(len(narrativas_asignadas)),
        "ruido_frac": (
            float((comentarios["_narrativa"] == "ninguna").mean())
            if len(comentarios)
            else 0.0
        ),
        "grupos_coordinados": int(
            comentarios.loc[comentarios["grupo"] != "", "grupo"].nunique()
        ),
        "cuentas_coordinadas": int(cuentas_coordinadas.sum()),
        "categorias": _conteo_categorias(comentarios),
        "costo": costo,
        "fecha_min": fecha_min,
        "fecha_max": fecha_max,
    }

    salida.mkdir(parents=True, exist_ok=True)
    _escribir_json(salida / "resumen.json", resumen)
    _escribir_json(salida / "fuentes.json", fuentes_json)
    _escribir_json(salida / "publicaciones.json", publicaciones_json)
    _escribir_json(salida / "narrativas.json", narrativas_json)
    _escribir_json(salida / "coordinacion.json", coordinacion_json)

    directorio_comentarios = salida / "comentarios"
    directorio_comentarios.mkdir(parents=True, exist_ok=True)
    for publicacion_id in publicaciones["publicacion_id"]:
        grupo = comentarios_por_publicacion.get(
            publicacion_id, comentarios.iloc[0:0]
        )
        registros = [
            _comentario_exportable(fila)
            for fila in grupo.to_dict(orient="records")
        ]
        _escribir_json(
            directorio_comentarios / f"{publicacion_id}.json",
            registros,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--conjunto",
        choices=("practica", "final"),
        default="practica",
    )
    parser.add_argument("--datos", type=Path)
    parser.add_argument("--entrega", type=Path)
    parser.add_argument(
        "--salida", type=Path, default=Path("dashboard/public/data")
    )
    argumentos = parser.parse_args()
    datos_default, entrega_default = {
        "practica": (Path("datos/practica"), Path("salida/practica_nexo")),
        "final": (Path("datos/final"), Path("entrega")),
    }[argumentos.conjunto]
    exportar(
        argumentos.datos or datos_default,
        argumentos.entrega or entrega_default,
        argumentos.salida,
        argumentos.conjunto,
    )


if __name__ == "__main__":
    main()
