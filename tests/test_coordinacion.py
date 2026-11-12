import networkx as nx
import pandas as pd

from nexo_signal.coordinacion import comunidades
from nexo_signal.coordinacion.senales import calcular_senales


def test_ed_exige_repeticion_en_ambas_cuentas():
    inicio = pd.Timestamp("2026-09-07T08:00:00Z")
    filas = [
        ("a1", "A", "frase compartida suficientemente larga", 0),
        ("a2", "A", "frase compartida suficientemente larga", 30),
        ("b1", "B", "frase compartida suficientemente larga", 60),
        ("c1", "C", "otra coincidencia suficientemente larga", 0),
        ("c2", "C", "otra coincidencia suficientemente larga", 30),
        ("d1", "D", "otra coincidencia suficientemente larga", 60),
        ("d2", "D", "otra coincidencia suficientemente larga", 90),
    ]
    comentarios = pd.DataFrame(
        [
            {
                "comentario_id": comentario_id,
                "publicacion_id": f"p-{comentario_id}",
                "cuenta_id": cuenta_id,
                "fecha_dt": inicio + pd.Timedelta(seconds=segundos),
                "respuesta_a": "",
                "core": core,
            }
            for comentario_id, cuenta_id, core, segundos in filas
        ]
    )

    senales, _ = calcular_senales(comentarios)
    assert senales["ed"].to_dict(orient="records") == [
        {"a": "C", "b": "D", "k": 2}
    ]


def test_descarta_grupos_demasiado_pequenos_tras_resolver_solapamientos(monkeypatch):
    tablas_senales = {
        nombre: pd.DataFrame(columns=["a", "b", "k"])
        for nombre in ("ec", "ed", "er")
    }
    monkeypatch.setattr(
        comunidades.senales, "calcular_senales", lambda comentarios: (tablas_senales, {})
    )
    monkeypatch.setattr(
        comunidades.grafo,
        "construir",
        lambda senales: (nx.Graph(), nx.Graph(), nx.Graph()),
    )
    candidatos = [
        {"canal": "T", "cuentas": {"a", "b", "c", "d"}, "id_prueba": "grande"},
        {"canal": "R", "cuentas": {"a", "b", "e", "f"}, "id_prueba": "pequeno"},
    ]
    monkeypatch.setattr(comunidades, "_candidatos", lambda temporal, respuestas: candidatos)
    monkeypatch.setattr(
        comunidades,
        "_medir_candidato",
        lambda candidato, union, cantidad: {
            **candidato,
            "densidad": 0.5,
            "ratio": 20 if candidato["id_prueba"] == "grande" else 11,
        },
    )
    monkeypatch.setattr(
        comunidades, "_expandir", lambda candidato, union, respuestas: candidato["cuentas"]
    )
    evidencia_recibida = {}

    def capturar_evidencia(miembros, detalle, comentarios, cuentas):
        evidencia_recibida.update({grupo: set(ids) for grupo, ids in miembros.items()})
        return pd.DataFrame(
            [{"grupo": grupo, "n_cuentas": len(ids)} for grupo, ids in miembros.items()]
        )

    monkeypatch.setattr(comunidades, "_evidencia", capturar_evidencia)
    grupos, evidencia, resumen = comunidades.analizar_coordinacion(
        pd.DataFrame(), pd.DataFrame()
    )

    assert grupos == {"a": "G1", "b": "G1", "c": "G1", "d": "G1"}
    assert evidencia_recibida == {"G1": {"a", "b", "c", "d"}}
    assert evidencia["n_cuentas"].tolist() == [4]
    assert resumen["grupos"] == 1
