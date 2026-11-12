import numpy as np
import pandas as pd

from nexo_signal import __main__ as pipeline
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
    _guardar_gzip(pd.DataFrame(filas), datos / "comentarios.csv.gz")
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
    assert len(comentarios) == 300
    assert comentarios["comentario_id"].tolist() == [f"c{i}" for i in range(300)]
    assert comentarios.loc[comentarios["comentario_id"].eq("c4"), "narrativa"].iloc[0] == ""
    cuentas = pd.read_csv(entrega / "cuentas.csv", dtype=str, keep_default_na=False)
    assert len(cuentas) == 11
    assert cuentas["cuenta_id"].tolist() == sorted(cuentas["cuenta_id"])
    narrativas = pd.read_csv(entrega / "narrativas.csv", dtype=str, keep_default_na=False)
    assert narrativas["narrativa"].tolist() == sorted(narrativas["narrativa"])
    limpios = pd.read_parquet(cache / "datos" / "comentarios.parquet")
    assert limpios.loc[limpios["comentario_id"].eq("c5"), "respuesta_a"].iloc[0] == ""
    assert metricas["conteos"]["comentarios"] == 300
    assert metricas["modelo"] == pipeline.embeddings.MODELO
    assert metricas["revision_modelo"] == pipeline.embeddings.REVISION
    resumen = validar_entrega(datos, entrega)
    assert resumen == {"filas_entrada": 303, "ids_unicos": 300, "filas_salida": 300}
