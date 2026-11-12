import pandas as pd

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
