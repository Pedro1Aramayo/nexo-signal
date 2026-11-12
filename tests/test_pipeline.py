import gzip

import numpy as np
import pandas as pd

from nexo_signal import __main__ as pipeline
from nexo_signal.ingesta.cargar import (
    ORDEN_ENTRADA,
    _leer_csv,
    _recuperar_rechazos,
    cargar,
)
from herramientas.validar_entrega import validar_entrega


def _guardar_gzip(df, ruta):
    df.to_csv(ruta, index=False, compression="gzip")


def test_pipeline_con_datos_sucios(tmp_path, monkeypatch):
    datos = tmp_path / "datos"
    datos.mkdir()
    entrega = tmp_path / "salida"
    cache = tmp_path / "cache"
    textos = [
        "La obra avanza con recursos confirmados",
        "La obra se detuvo por recortes financieros",
    ]
    filas = []
    for i in range(300):
        texto = textos[i % 2]
        padre = ""
        if i == 0:
            texto = ""
        elif i % 30 == 1:
            texto, padre = "Tal cual", f"c{i - 1}"
        elif i == 5:
            padre = "id-inexistente"
        fecha = "fecha-invalida" if i == 4 else f"2026-09-{7 + (i % 3):02d}T08:00:00-03:00"
        filas.append({
            "comentario_id": f"c{i}", "publicacion_id": "p1",
            "cuenta_id": f"cuenta-{i % 10}", "fecha": fecha,
            "texto": texto, "respuesta_a": padre, "me_gusta": "0",
        })
    filas.extend([
        {"comentario_id": "", "publicacion_id": "p1", "cuenta_id": "cuenta-1",
         "fecha": "2026-09-07T08:00:00-03:00", "texto": "sin id", "respuesta_a": "", "me_gusta": "0"},
        {"comentario_id": "sin-cuenta", "publicacion_id": "p1", "cuenta_id": "",
         "fecha": "2026-09-07T08:00:00-03:00", "texto": "sin cuenta", "respuesta_a": "", "me_gusta": "0"},
        {"comentario_id": "c10", "publicacion_id": "p1", "cuenta_id": "cuenta-0",
         "fecha": "2026-09-07T08:00:00-03:00", "texto": "duplicado", "respuesta_a": "", "me_gusta": "0"},
    ])
    archivo_comentarios = datos / "comentarios.csv"
    pd.DataFrame(filas[:150]).to_csv(archivo_comentarios, index=False)
    with archivo_comentarios.open("a", encoding="utf-8") as salida:
        salida.write(
            "malformado,p1,cuenta-1,2026-09-07T08:00:00-03:00,Texto,,0,extra\n"
        )
    pd.DataFrame(filas[150:]).to_csv(
        archivo_comentarios, index=False, header=False, mode="a"
    )
    _guardar_gzip(
        pd.DataFrame({"cuenta_id": [f"cuenta-{i}" for i in range(10)] + ["sin-comentarios"],
                      "usuario": ["u"] * 11, "fecha_creacion": [""] * 11,
                      "seguidores": ["0"] * 11, "siguiendo": ["0"] * 11}),
        datos / "cuentas.csv.gz",
    )
    _guardar_gzip(pd.DataFrame({"publicacion_id": ["p1"], "fuente_id": ["f1"],
                                "fecha": ["2026-09-07"], "titular": ["obra"]}),
                 datos / "publicaciones.csv.gz")
    pd.DataFrame({"fuente_id": ["f1"], "nombre": ["Fuente"], "tipo": ["medio"]}).to_csv(
        datos / "fuentes.csv", index=False
    )

    def fake_embeddings(cores, cache_path):
        vectores = {}
        for core in cores:
            if "avanza" in core:
                vectores[core] = np.array([1.0, 0.0], dtype=np.float32)
            elif "detuvo" in core:
                vectores[core] = np.array([0.0, 1.0], dtype=np.float32)
            else:
                vectores[core] = np.array([0.7, 0.7], dtype=np.float32)
        return vectores

    monkeypatch.setattr(pipeline.embeddings, "calcular_embeddings", fake_embeddings)
    metricas = pipeline.ejecutar(datos, entrega, cache)

    assert {p.name for p in entrega.iterdir() if p.is_file()} == {
        "comentarios.csv", "narrativas.csv", "cuentas.csv", "costo.json"
    }
    assert (entrega / "evidencia" / "metricas.json").exists()
    for nombre in ("comentarios.csv", "narrativas.csv", "cuentas.csv", "costo.json"):
        assert (entrega / nombre).exists()
    comentarios = pd.read_csv(entrega / "comentarios.csv", dtype=str, keep_default_na=False)
    assert list(comentarios.columns) == ["comentario_id", "narrativa", "postura"]
    assert len(comentarios) == 301
    assert comentarios["comentario_id"].tolist() == [
        *(f"c{i}" for i in range(150)), "malformado",
        *(f"c{i}" for i in range(150, 300)),
    ]
    assert comentarios.loc[comentarios["comentario_id"].eq("c4"), "narrativa"].iloc[0] == ""
    assert comentarios.loc[
        comentarios["comentario_id"].eq("malformado"), "narrativa"
    ].iloc[0] == ""
    cuentas = pd.read_csv(entrega / "cuentas.csv", dtype=str, keep_default_na=False)
    assert len(cuentas) == 11
    assert cuentas["cuenta_id"].tolist() == sorted(cuentas["cuenta_id"])
    narrativas = pd.read_csv(entrega / "narrativas.csv", dtype=str, keep_default_na=False)
    assert narrativas["narrativa"].tolist() == sorted(narrativas["narrativa"])
    limpios = pd.read_parquet(cache / "datos" / "comentarios.parquet")
    assert limpios.loc[limpios["comentario_id"].eq("c5"), "respuesta_a"].iloc[0] == ""
    assert metricas["conteos"]["comentarios"] == 301
    assert metricas["modelo"] == pipeline.embeddings.MODELO
    assert metricas["revision_modelo"] == pipeline.embeddings.REVISION
    assert metricas["ingesta"] == {
        "filas_entrada": 304,
        "comentarios_rechazados": 1,
        "comentarios_recuperados": 1,
        "esquema_alternativo": [],
    }
    assert limpios.loc[
        limpios["comentario_id"].eq("malformado"), "texto"
    ].iloc[0] == ""
    resumen = validar_entrega(datos, entrega)
    assert resumen == {"filas_entrada": 304, "ids_unicos": 301, "filas_salida": 301}


def test_ingesta_esquema_alternativo_respeta_nombres_y_columnas_extra(tmp_path):
    datos = tmp_path / "datos"
    datos.mkdir()
    cache = tmp_path / "cache"
    comentarios = datos / "comentarios.csv.gz"
    with gzip.open(comentarios, "wt", encoding="utf-8", newline="") as archivo:
        archivo.write(
            "\ufeff texto ,cuenta_id,comentario_id,publicacion_id,fecha,respuesta_a,extra\n"
            "Texto correcto,cuenta-1,c1,p1,2026-09-07T08:00:00-03:00,,valor-extra\n"
        )
    pd.DataFrame(
        [{"publicacion_id": "p1", "fuente_id": "f1", "fecha": "2026-09-07", "titular": "t"}]
    ).to_csv(datos / "publicaciones.csv", index=False)
    pd.DataFrame(
        [{"fuente_id": "f1", "nombre": "Fuente", "tipo": "medio"}]
    ).to_csv(datos / "fuentes.csv", index=False)
    pd.DataFrame(
        [{
            "cuenta_id": "cuenta-1", "usuario": "u", "fecha_creacion": "",
            "seguidores": "0", "siguiendo": "0",
        }]
    ).to_csv(datos / "cuentas.csv", index=False)

    tablas = cargar(datos, cache)

    fila = tablas["comentarios"].iloc[0]
    assert fila["comentario_id"] == "c1"
    assert fila["cuenta_id"] == "cuenta-1"
    assert fila["texto"] == "Texto correcto"
    assert fila["me_gusta"] == ""
    assert pd.read_parquet(cache / "comentarios.parquet").loc[0, "extra"] == "valor-extra"
    assert tablas["comentarios"].attrs["ingesta"]["esquema_alternativo"] == [
        "comentarios"
    ]


def test_ingesta_esquema_alternativo_recupera_id_por_encabezado(tmp_path):
    comentarios = tmp_path / "comentarios.csv"
    with comentarios.open("w", encoding="utf-8", newline="") as archivo:
        archivo.write(
            "texto,comentario_id,publicacion_id,cuenta_id,fecha,respuesta_a,me_gusta\n"
        )
        for i in range(21_000):
            archivo.write(
                f"Texto {i},c{i},p1,cuenta-1,2026-09-07T08:00:00-03:00,,0\n"
            )
        archivo.write(
            "Texto malformado,id-real,p1,cuenta-1,2026-09-07T08:00:00-03:00,,0,extra\n"
        )

    datos, rechazos, encabezado, alternativo = _leer_csv(comentarios, "comentarios")
    assert alternativo
    assert encabezado.index("comentario_id") == 1
    assert len(rechazos) == 1

    comentarios_recuperados, cantidad = _recuperar_rechazos(
        datos, rechazos, encabezado.index("comentario_id")
    )
    fila = comentarios_recuperados.loc[
        comentarios_recuperados["comentario_id"].eq("id-real")
    ].iloc[0]
    assert cantidad == 1
    assert fila["texto"] == ""

    vacios = pd.DataFrame(
        {"comentario_id": [""], ORDEN_ENTRADA: [1]}
    )
    sin_indice, cantidad_sin_indice = _recuperar_rechazos(
        vacios, pd.DataFrame([{"line": 2, "csv_line": "texto,id-real"}]), None
    )
    assert cantidad_sin_indice == 0
    assert not sin_indice["comentario_id"].eq("id-real").any()
