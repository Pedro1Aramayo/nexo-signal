import argparse
import json
import math
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

from nexo_signal.ingesta.cargar import cargar


ARCHIVOS = {
    "comentarios.csv": ["comentario_id", "narrativa", "postura"],
    "narrativas.csv": ["narrativa", "titulo", "frases_clave", "fecha_origen"],
    "cuentas.csv": ["cuenta_id", "grupo"],
    "costo.json": [
        "comentarios_procesados",
        "segundos",
        "tokens_ia",
        "usd_ia",
        "usd_por_mil_comentarios",
        "hardware",
        "almacenamiento",
        "notas",
    ],
}
RUIDO = {"", "ninguna", "none", "null"}


def _leer_csv(
    ruta: Path, columnas: list[str], errores: list[str]
) -> pd.DataFrame | None:
    if not ruta.is_file():
        errores.append(f"Falta {ruta.name}")
        return None
    tabla = pd.read_csv(ruta, dtype=str, keep_default_na=False)
    if list(tabla.columns) != columnas:
        errores.append(f"{ruta.name}: columnas {list(tabla.columns)!r}, esperadas {columnas!r}")
    return tabla


def _asegurar_columnas(tabla: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    for columna in columnas:
        if columna not in tabla:
            tabla[columna] = ""
    return tabla


def _validar_costo(ruta: Path, cantidad: int, errores: list[str]) -> None:
    if not ruta.is_file():
        errores.append("Falta costo.json")
        return
    try:
        costo = json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        errores.append(f"costo.json no es JSON válido: {exc}")
        return
    if not isinstance(costo, dict) or set(costo) != set(ARCHIVOS["costo.json"]):
        errores.append(f"costo.json debe tener exactamente estas claves: {ARCHIVOS['costo.json']}")
        return
    enteros = ("comentarios_procesados", "tokens_ia")
    numeros = ("segundos", "usd_ia", "usd_por_mil_comentarios")
    for clave in enteros:
        if type(costo[clave]) is not int or costo[clave] < 0:
            errores.append(f"costo.json: {clave} debe ser un entero no negativo")
    for clave in numeros:
        valor = costo[clave]
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor) or valor < 0:
            errores.append(f"costo.json: {clave} debe ser un número finito no negativo")
    for clave in ("hardware", "almacenamiento", "notas"):
        if not isinstance(costo[clave], str):
            errores.append(f"costo.json: {clave} debe ser texto")
    if costo["comentarios_procesados"] != cantidad:
        errores.append(
            f"costo.json: comentarios_procesados={costo['comentarios_procesados']}, "
            f"esperado={cantidad}"
        )


def validar_entrega(datos: Path, entrega: Path) -> dict[str, int]:
    if not entrega.is_dir():
        raise ValueError(f"No existe el directorio de entrega: {entrega}")
    errores = []
    archivos_raiz = {ruta.name for ruta in entrega.iterdir() if ruta.is_file()}
    directorios_raiz = {ruta.name for ruta in entrega.iterdir() if ruta.is_dir()}
    esperados = set(ARCHIVOS)
    if archivos_raiz != esperados:
        errores.append(
            f"Archivos en raíz: faltan {sorted(esperados - archivos_raiz)}, "
            f"sobran {sorted(archivos_raiz - esperados)}"
        )
    if directorios_raiz != {"evidencia"}:
        errores.append(
            f"Directorios en raíz: esperados ['evidencia'], encontrados {sorted(directorios_raiz)}"
        )

    with tempfile.TemporaryDirectory(prefix="nexo-validar-") as directorio_cache:
        tablas = cargar(datos, Path(directorio_cache))
    entrada_comentarios = tablas["comentarios"]
    entrada_cuentas = tablas["cuentas"]
    input_rows = int(entrada_comentarios.attrs.get("ingesta", {}).get(
        "filas_entrada", len(entrada_comentarios)
    ))
    ids_entrada = entrada_comentarios["comentario_id"].tolist()
    cuentas_entrada = entrada_cuentas["cuenta_id"].tolist()

    comentarios = _leer_csv(
        entrega / "comentarios.csv", ARCHIVOS["comentarios.csv"], errores
    )
    narrativas = _leer_csv(
        entrega / "narrativas.csv", ARCHIVOS["narrativas.csv"], errores
    )
    cuentas = _leer_csv(entrega / "cuentas.csv", ARCHIVOS["cuentas.csv"], errores)
    if comentarios is None:
        comentarios = pd.DataFrame(columns=ARCHIVOS["comentarios.csv"])
    if narrativas is None:
        narrativas = pd.DataFrame(columns=ARCHIVOS["narrativas.csv"])
    if cuentas is None:
        cuentas = pd.DataFrame(columns=ARCHIVOS["cuentas.csv"])
    comentarios = _asegurar_columnas(comentarios, ARCHIVOS["comentarios.csv"])
    narrativas = _asegurar_columnas(narrativas, ARCHIVOS["narrativas.csv"])
    cuentas = _asegurar_columnas(cuentas, ARCHIVOS["cuentas.csv"])

    salida_ids = comentarios["comentario_id"].tolist()
    faltantes = set(ids_entrada) - set(salida_ids)
    desconocidos = set(salida_ids) - set(ids_entrada)
    duplicados = comentarios.loc[
        comentarios["comentario_id"].duplicated(), "comentario_id"
    ].unique()
    if faltantes or len(duplicados) or len(salida_ids) != len(ids_entrada):
        errores.append(
            f"comentarios.csv no tiene una fila por id: faltan {len(faltantes)}, "
            f"duplicados {len(duplicados)}"
        )
    if desconocidos:
        errores.append(f"comentarios.csv contiene {len(desconocidos)} ids desconocidos")
    if salida_ids != ids_entrada:
        errores.append("comentarios.csv no conserva el orden de entrada")

    etiquetas_comentarios = comentarios["narrativa"].astype(str).str.strip()
    no_ruido = ~etiquetas_comentarios.str.lower().isin(RUIDO)
    posturas_invalidas = comentarios.loc[
        no_ruido & ~comentarios["postura"].isin({"apoya", "rechaza"})
    ]
    if len(posturas_invalidas):
        errores.append(f"Hay {len(posturas_invalidas)} posturas inválidas")
    etiquetas_salida = set(etiquetas_comentarios[no_ruido])
    etiquetas_narrativas = set(narrativas["narrativa"].astype(str).str.strip())
    if etiquetas_salida != etiquetas_narrativas:
        errores.append(
            "Las etiquetas de comentarios.csv y narrativas.csv no coinciden"
        )
    if narrativas["narrativa"].duplicated().any():
        errores.append("narrativas.csv contiene etiquetas duplicadas")
    etiquetas_ordenadas = narrativas["narrativa"].tolist()
    if etiquetas_ordenadas != sorted(etiquetas_ordenadas):
        errores.append("narrativas.csv no está ordenado por etiqueta")
    for fila, valor in enumerate(narrativas["fecha_origen"]):
        try:
            fecha = datetime.fromisoformat(valor.replace("Z", "+00:00"))
            if fecha.tzinfo is None or fecha.utcoffset() is None:
                raise ValueError("sin zona horaria")
        except (ValueError, AttributeError):
            errores.append(f"narrativas.csv fila {fila + 2}: fecha_origen no es ISO con zona horaria")

    salida_cuentas = cuentas["cuenta_id"].tolist()
    cuentas_faltantes = set(cuentas_entrada) - set(salida_cuentas)
    cuentas_desconocidas = set(salida_cuentas) - set(cuentas_entrada)
    cuentas_duplicadas = cuentas.loc[
        cuentas["cuenta_id"].duplicated(), "cuenta_id"
    ].unique()
    if (
        cuentas_faltantes
        or len(cuentas_duplicadas)
        or len(salida_cuentas) != len(cuentas_entrada)
    ):
        errores.append(
            f"cuentas.csv no tiene una fila por cuenta: faltan {len(cuentas_faltantes)}, "
            f"duplicadas {len(cuentas_duplicadas)}"
        )
    if cuentas_desconocidas:
        errores.append(f"cuentas.csv contiene {len(cuentas_desconocidas)} cuentas desconocidas")
    if salida_cuentas != sorted(cuentas_entrada):
        errores.append("cuentas.csv no está ordenado por cuenta_id")

    _validar_costo(entrega / "costo.json", len(ids_entrada), errores)
    resumen = {
        "filas_entrada": input_rows,
        "ids_unicos": len(ids_entrada),
        "filas_salida": len(salida_ids),
    }
    if errores:
        raise ValueError("\n".join(errores))
    return resumen


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida los archivos oficiales de entrega.")
    parser.add_argument("--datos", type=Path, required=True)
    parser.add_argument("--entrega", type=Path, required=True)
    args = parser.parse_args()
    try:
        resumen = validar_entrega(args.datos, args.entrega)
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(1, f"Error de validación: {exc}\n")
    print(
        "Validación correcta: "
        f"filas de entrada={resumen['filas_entrada']}, "
        f"ids únicos tras limpieza={resumen['ids_unicos']}, "
        f"filas de salida={resumen['filas_salida']}."
    )


if __name__ == "__main__":
    main()
