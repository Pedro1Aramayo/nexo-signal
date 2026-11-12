from pathlib import Path

from herramientas import demo


def _crear_datos_entrega(tmp_path: Path):
    datos = tmp_path / "datos"
    entrega = tmp_path / "entrega"
    evidencia = entrega / "evidencia"
    datos.mkdir()
    evidencia.mkdir(parents=True)

    (datos / "comentarios.csv").write_text(
        "comentario_id,cuenta_id,fecha,texto,respuesta_a\n"
        "id1,cuenta-1,2026-09-07T08:00:00-03:00,"
        "Este comentario original tiene suficiente texto para la demo,\n"
        "id1,cuenta-2,2026-09-07T08:00:00-03:00,"
        "Este duplicado no debe multiplicar los resultados,\n"
        "id2,cuenta-2,2026-09-07T09:00:00-03:00,"
        "Otro comentario suficientemente largo para la demostración,\n"
        "malformado,cuenta-1,2026-09-07T10:00:00-03:00,Texto malo,,extra\n",
        encoding="utf-8",
    )
    (entrega / "comentarios.csv").write_text(
        "comentario_id,narrativa,postura\n"
        "id1,n01,apoya\n"
        "id2,n01,rechaza\n",
        encoding="utf-8",
    )
    (entrega / "narrativas.csv").write_text(
        "narrativa,titulo,fecha_origen,frases_clave\n"
        "n01,Una narrativa,2026-09-07T00:00:00-03:00,frase|clave\n",
        encoding="utf-8",
    )
    (entrega / "cuentas.csv").write_text(
        "cuenta_id,grupo\n"
        "cuenta-1,G1\n"
        "cuenta-1,G2\n"
        "cuenta-2,G1\n",
        encoding="utf-8",
    )
    (entrega / "costo.json").write_text(
        '{"segundos": 1.2, "usd_ia": 0, "hardware": "prueba"}',
        encoding="utf-8",
    )
    (evidencia / "grupos_coordinados.csv").write_text(
        "grupo,n_cuentas,canal,densidad,ratio,"
        "mediana_dias_cuenta_al_primer_comentario,frac_nocturna,"
        "n_publicaciones,ejemplo_texto\n"
        "G1,2,T,0.50,12,,0.25,1,Texto de ejemplo\n",
        encoding="utf-8",
    )
    return datos, entrega


def test_leer_omite_malformadas_y_deduplica_antes_de_unir(tmp_path):
    datos, entrega = _crear_datos_entrega(tmp_path)

    df, narr, cue, evidencia, costo = demo.leer(datos, entrega)

    assert df["comentario_id"].tolist() == ["id1", "id2"]
    assert len(cue) == 2
    assert len(narr) == 1
    assert evidencia is not None
    assert costo["segundos"] == 1.2

    resultado = demo.render(df, narr, cue, evidencia, costo, "prueba")
    salida = tmp_path / "demo.html"
    salida.write_text(resultado, encoding="utf-8")
    assert salida.exists()
    assert "<b>2</b><span>comentarios analizados</span>" in resultado
    assert "<td>0.50</td>" in resultado
    assert "<td>12×</td>" in resultado
    assert "<td>—</td>" in resultado
    assert "<td>25%</td>" in resultado

    for columna, valor in (
        ("densidad", ""),
        ("ratio", "NaN"),
        ("frac_nocturna", "no-numérico"),
    ):
        evidencia_invalida = evidencia.copy()
        evidencia_invalida[columna] = valor
        html = demo.render(df, narr, cue, evidencia_invalida, costo, "prueba")
        assert "—" in html
