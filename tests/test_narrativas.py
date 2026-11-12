import numpy as np
import pandas as pd

from nexo_signal.narrativas.describir import describir
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
            "core": ["core"] * len(tiempos),
            "fecha_dt": tiempos,
        }
    )

    assert fechas_origen(comentarios, {"core": np.array([1.0, 0.0])})["n01"] == (
        "2026-09-07T13:00:00-03:00"
    )


def test_origen_descarta_fringe_ortogonal_al_nucleo():
    inicio = pd.Timestamp("2026-09-07T08:00:00-03:00")
    filas = [
        {
            "narrativa": "n01",
            "respuesta_corta": False,
            "core": f"fringe-{i}",
            "fecha_dt": inicio + pd.Timedelta(hours=i),
        }
        for i in range(3)
    ]
    inicio_central = inicio + pd.Timedelta(days=7)
    filas.extend(
        {
            "narrativa": "n01",
            "respuesta_corta": False,
            "core": "central",
            "fecha_dt": inicio_central + pd.Timedelta(minutes=15 * i),
        }
        for i in range(6)
    )
    vectores = {
        **{f"fringe-{i}": np.array([0.0, 1.0]) for i in range(3)},
        "central": np.array([1.0, 0.0]),
    }

    assert fechas_origen(pd.DataFrame(filas), vectores)["n01"] == (
        "2026-09-14T08:00:00-03:00"
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


def test_piso_de_tamano_se_aplica_despues_de_filtrar_cores_ruidosos():
    inicio = pd.Timestamp("2026-09-07T08:00:00-03:00")
    filas = [
        {
            "comentario_id": f"pequeno-{i}",
            "core": "core pequeño",
            "respuesta_a": "externo",
            "n_tokens": 5,
            "fecha_dt": inicio + pd.Timedelta(minutes=i),
        }
        for i in range(20)
    ]
    filas.extend(
        {
            "comentario_id": f"ruido-{i}",
            "core": "core esporadico",
            "respuesta_a": "",
            "n_tokens": 5,
            "fecha_dt": inicio + pd.Timedelta(minutes=30 + i),
        }
        for i in range(15)
    )
    filas.extend(
        {
            "comentario_id": f"grande-{i}",
            "core": "core grande",
            "respuesta_a": "externo",
            "n_tokens": 5,
            "fecha_dt": inicio + pd.Timedelta(minutes=60 + i),
        }
        for i in range(30)
    )
    filas.append(
        {
            "comentario_id": "respuesta-corta",
            "core": "",
            "respuesta_a": "pequeno-0",
            "n_tokens": 2,
            "fecha_dt": inicio,
        }
    )

    resultado, etiquetas = asignar(
        pd.DataFrame(filas),
        {"core pequeño": 0, "core esporadico": 0, "core grande": 1},
    )

    assert resultado.loc[
        resultado["comentario_id"].str.startswith("pequeno-"), "narrativa"
    ].eq("").all()
    assert resultado.loc[
        resultado["comentario_id"].str.startswith("ruido-"), "narrativa"
    ].eq("").all()
    assert resultado.loc[
        resultado["comentario_id"].eq("respuesta-corta"), "narrativa"
    ].iloc[0] == ""
    assert etiquetas == {1: "n01"}
    assert resultado.loc[
        resultado["comentario_id"].str.startswith("grande-"), "narrativa"
    ].eq("n01").all()


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
    origen = fechas_origen(resultado, {"core repetido": np.array([1.0, 0.0])})
    assert resultado["narrativa"].ne("").any()
    assert all(origen[etiqueta] for etiqueta in resultado["narrativa"].unique() if etiqueta)


def test_titulo_usa_core_central_y_texto_original_mas_frecuente():
    inicio = pd.Timestamp("2026-09-07T08:00:00-03:00")
    textos = [
        "  Texto   central repetido!  "
    ] * 5 + ["Otra variante central"] * 3 + ["Texto de fringe"] * 2
    cores = ["central"] * 8 + ["fringe"] * 2
    comentarios = pd.DataFrame(
        {
            "narrativa": ["n01"] * 10,
            "respuesta_corta": [False] * 10,
            "core": cores,
            "postura": ["apoya"] * 10,
            "n_tokens": [5] * 10,
            "texto": textos,
            "fecha_dt": [inicio + pd.Timedelta(minutes=i) for i in range(10)],
        }
    )
    vectores = {
        "central": np.array([1.0, 0.0]),
        "fringe": np.array([0.0, 1.0]),
    }

    resultado = describir(comentarios, vectores)

    assert resultado.loc[0, "titulo"] == "Texto central repetido!"


def test_respuestas_cortas_no_arrastran_el_centroide_del_origen():
    inicio = pd.Timestamp("2026-09-07T08:00:00-03:00")
    filas = [
        {
            "narrativa": "n01",
            "respuesta_corta": False,
            "core": f"fringe-{i}",
            "fecha_dt": inicio + pd.Timedelta(hours=i),
        }
        for i in range(3)
    ]
    inicio_central = inicio + pd.Timedelta(days=7)
    filas.extend(
        {
            "narrativa": "n01",
            "respuesta_corta": False,
            "core": "central",
            "fecha_dt": inicio_central + pd.Timedelta(minutes=15 * i),
        }
        for i in range(6)
    )
    filas.extend(
        {
            "narrativa": "n01",
            "respuesta_corta": True,
            "core": "respuesta",
            "fecha_dt": inicio + pd.Timedelta(hours=3, minutes=i),
        }
        for i in range(20)
    )
    vectores = {
        **{f"fringe-{i}": np.array([0.0, 1.0]) for i in range(3)},
        "central": np.array([1.0, 0.0]),
        "respuesta": np.array([0.0, 1.0]),
    }

    assert fechas_origen(pd.DataFrame(filas), vectores)["n01"] == (
        "2026-09-14T08:00:00-03:00"
    )
