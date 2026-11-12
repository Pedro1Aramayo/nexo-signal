import pandas as pd

from nexo_signal.narrativas.origen import fechas_origen
from nexo_signal.narrativas.ruido import asignar


def test_origen_usa_ventana_seis_horas_semicerrada():
    inicio = pd.Timestamp("2026-09-07T08:00:00-03:00")
    tiempos = [
        inicio,
        inicio + pd.Timedelta(hours=5),
        inicio + pd.Timedelta(hours=6),
        inicio + pd.Timedelta(hours=10),
        inicio + pd.Timedelta(hours=10, minutes=1),
        inicio + pd.Timedelta(hours=10, minutes=2),
    ]
    comentarios = pd.DataFrame(
        {
            "narrativa": ["n01"] * len(tiempos),
            "respuesta_corta": [False] * len(tiempos),
            "fecha_dt": tiempos,
        }
    )

    assert fechas_origen(comentarios)["n01"] == (
        "2026-09-07T13:00:00-03:00"
    )


def test_cluster_pequeno_es_ruido_y_el_origen_no_queda_vacio():
    inicio = pd.Timestamp("2026-09-07T08:00:00-03:00")
    filas = [
        {
            "comentario_id": f"c{i}",
            "core": "core repetido",
            "respuesta_a": "externo",
            "n_tokens": 4,
            "fecha_dt": inicio + pd.Timedelta(hours=7 * i),
        }
        for i in range(29)
    ]
    filas.append(
        {
            "comentario_id": "respuesta",
            "core": "",
            "respuesta_a": "c0",
            "n_tokens": 2,
            "fecha_dt": inicio,
        }
    )

    resultado, _ = asignar(pd.DataFrame(filas), {"core repetido": 0})
    assert resultado.loc[resultado["comentario_id"].eq("respuesta"), "narrativa"].iloc[0] == ""
    assert resultado.loc[resultado["narrativa"].ne(""), "narrativa"].empty
    assert resultado["narrativa"].eq("").all()


def test_narrativa_emitida_tiene_fecha_origen():
    inicio = pd.Timestamp("2026-09-07T08:00:00-03:00")
    filas = [
        {
            "comentario_id": f"c{i}",
            "core": "core repetido",
            "respuesta_a": "externo",
            "n_tokens": 4,
            "fecha_dt": inicio + pd.Timedelta(hours=7 * i),
        }
        for i in range(30)
    ]

    resultado, _ = asignar(pd.DataFrame(filas), {"core repetido": 0})
    origen = fechas_origen(resultado)
    assert resultado["narrativa"].ne("").any()
    assert all(origen[etiqueta] for etiqueta in resultado["narrativa"].unique() if etiqueta)
