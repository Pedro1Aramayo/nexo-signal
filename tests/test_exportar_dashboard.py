import json
from pathlib import Path

import pandas as pd
import pytest

from herramientas.exportar_dashboard import categoria, exportar


@pytest.mark.parametrize(
    ("texto", "esperada"),
    [
        ("Deberían arreglar esto", "sugerencia"),
        ("¿Por qué no arreglan…?", "sugerencia"),
        ("Qué vergüenza", "queja"),
        ("Nadie hace nada?", "queja"),
        ("¿Cuándo llega el agua?", "consulta"),
        ("Hay que pedir turno por telefono o presencial?", "consulta"),
        ("Gracias, excelente noticia", "elogio"),
        ("con el nuevo sistema online mejoró bastante", "elogio"),
        ("Qué bronca, siempre igual", "queja"),
        ("QUÉ DÍA EH", "otro"),
        ("", "otro"),
    ],
)
def test_categoria(texto, esperada):
    assert categoria(texto) == esperada


def _guardar_tabla(frame: pd.DataFrame, ruta: Path):
    frame.to_csv(
        ruta,
        index=False,
        compression="gzip" if ruta.name.endswith(".gz") else None,
    )


def test_exporta_jsons_y_comentarios_por_publicacion(tmp_path):
    datos = tmp_path / "datos"
    entrega = tmp_path / "entrega"
    salida = tmp_path / "export"
    (entrega / "evidencia").mkdir(parents=True)
    datos.mkdir()

    _guardar_tabla(
        pd.DataFrame([{"fuente_id": "f1", "nombre": "Fuente", "tipo": "medio"}]),
        datos / "fuentes.csv",
    )
    _guardar_tabla(
        pd.DataFrame([{
            "publicacion_id": "p1",
            "fuente_id": "f1",
            "fecha": "2026-09-07T08:00:00-03:00",
            "titular": "Un título",
        }]),
        datos / "publicaciones.csv.gz",
    )
    _guardar_tabla(
        pd.DataFrame([
            {
                "comentario_id": "c1",
                "publicacion_id": "p1",
                "cuenta_id": "u1",
                "fecha": "2026-09-07T08:01:00-03:00",
                "texto": "¿Por qué no arreglan el camino?",
                "respuesta_a": "",
                "me_gusta": "3",
            },
            {
                "comentario_id": "c2",
                "publicacion_id": "p1",
                "cuenta_id": "u2",
                "fecha": "2026-09-07T08:02:00-03:00",
                "texto": "Texto neutral",
                "respuesta_a": "c1",
                "me_gusta": "1",
            },
            {
                "comentario_id": "c1",
                "publicacion_id": "p1",
                "cuenta_id": "u1",
                "fecha": "2026-09-07T08:03:00-03:00",
                "texto": "Comentario duplicado",
                "respuesta_a": "",
                "me_gusta": "99",
            },
            {
                "comentario_id": "c9",
                "publicacion_id": "p1",
                "cuenta_id": "u2",
                "fecha": "2026-09-09T08:01:00-03:00",
                "texto": "Texto neutral",
                "respuesta_a": "",
                "me_gusta": "0",
            },
        ] + [
            {
                "comentario_id": f"c{i}",
                "publicacion_id": "p1",
                "cuenta_id": "u2",
                "fecha": f"2026-09-07T08:{i + 2:02d}:00-03:00",
                "texto": "Texto neutral",
                "respuesta_a": "",
                "me_gusta": "0",
            }
            for i in range(3, 9)
        ]),
        datos / "comentarios.csv.gz",
    )
    _guardar_tabla(
        pd.DataFrame([
            {
                "cuenta_id": "u1",
                "usuario": "usuario1",
                "fecha_creacion": "2020-01-01",
                "seguidores": "123",
                "siguiendo": "45",
            },
            {
                "cuenta_id": "u2",
                "usuario": "usuario2",
                "fecha_creacion": "2021-01-01",
                "seguidores": "67",
                "siguiendo": "89",
            },
        ]),
        datos / "cuentas.csv.gz",
    )

    _guardar_tabla(
        pd.DataFrame([
            {"comentario_id": "c1", "narrativa": "n01", "postura": "apoya"},
            {"comentario_id": "c2", "narrativa": "", "postura": ""},
            {"comentario_id": "c9", "narrativa": "n01", "postura": "apoya"},
        ] + [
            {
                "comentario_id": f"c{i}",
                "narrativa": f"n{i - 1:02d}",
                "postura": "apoya",
            }
            for i in range(3, 9)
        ]),
        entrega / "comentarios.csv",
    )
    _guardar_tabla(
        pd.DataFrame([{
            "narrativa": "n01",
            "titulo": "Narrativa de prueba",
            "frases_clave": "agua|camino",
            "fecha_origen": "2026-09-07T08:01:00-03:00",
        }] + [
            {
                "narrativa": f"n{i:02d}",
                "titulo": f"Narrativa {i}",
                "frases_clave": "agua|camino",
                "fecha_origen": "2026-09-07T08:01:00-03:00",
            }
            for i in range(2, 8)
        ]),
        entrega / "narrativas.csv",
    )
    _guardar_tabla(
        pd.DataFrame([
            {"cuenta_id": "u1", "grupo": "G1"},
            {"cuenta_id": "u2", "grupo": ""},
        ]),
        entrega / "cuentas.csv",
    )
    (entrega / "costo.json").write_text(
        json.dumps({"segundos": 1.25, "usd_ia": 0}, ensure_ascii=False),
        encoding="utf-8",
    )
    _guardar_tabla(
        pd.DataFrame([{
            "grupo": "G1",
            "n_cuentas": "1",
            "canal": "T",
            "densidad": "1.0",
            "ratio": "12.5",
            "mediana_dias_cuenta_al_primer_comentario": "",
            "mediana_seguidores": "123",
            "frac_nocturna": "0.25",
            "n_publicaciones": "1",
            "ejemplo_texto": "¿Por qué no arreglan el camino?",
        }]),
        entrega / "evidencia" / "grupos_coordinados.csv",
    )

    exportar(datos, entrega, salida, conjunto="final")

    resumen = json.loads((salida / "resumen.json").read_text(encoding="utf-8"))
    assert resumen["conjunto"] == "final"
    assert resumen["dataset"] == "Set final QualyData (sintético)"
    assert resumen["comentarios"] == 9
    assert resumen["publicaciones"] == 1
    assert resumen["fuentes"] == 1
    assert resumen["cuentas"] == 2
    assert resumen["narrativas"] == 7
    assert resumen["grupos_coordinados"] == 1
    assert resumen["cuentas_coordinadas"] == 1
    assert resumen["categorias"] == {
        "sugerencia": 1,
        "queja": 0,
        "consulta": 0,
        "elogio": 0,
        "otro": 8,
    }

    fuente = json.loads((salida / "fuentes.json").read_text(encoding="utf-8"))[0]
    assert fuente["plataforma_demo"] == "instagram"
    assert fuente["publicaciones"] == 1
    assert fuente["comentarios"] == 9

    publicacion = json.loads(
        (salida / "publicaciones.json").read_text(encoding="utf-8")
    )[0]
    assert publicacion["comentarios"] == 9
    assert publicacion["coordinados"] == 1
    assert publicacion["ruido"] == 1
    assert publicacion["me_gusta_total"] == 4
    assert [n["narrativa"] for n in publicacion["narrativas"]] == [
        f"n{i:02d}" for i in range(1, 8)
    ]
    assert [n["n"] for n in publicacion["narrativas"]] == [2, 1, 1, 1, 1, 1, 1]

    narrativa = json.loads(
        (salida / "narrativas.json").read_text(encoding="utf-8")
    )[0]
    assert narrativa["total"] == 2
    assert narrativa["organico_total"] == 1
    assert narrativa["coordinados"] == 1
    assert narrativa["serie"] == [
        {"dia": "2026-09-07", "total": 1, "organico": 0},
        {"dia": "2026-09-08", "total": 0, "organico": 0},
        {"dia": "2026-09-09", "total": 1, "organico": 1},
    ]

    grupo = json.loads(
        (salida / "coordinacion.json").read_text(encoding="utf-8")
    )[0]
    assert grupo["densidad"] == 1
    assert grupo["mediana_dias_cuenta_al_primer_comentario"] is None
    assert grupo["cuentas"][0]["usuario"] == "usuario1"
    assert grupo["comentarios"] == 1

    comentarios = json.loads(
        (salida / "comentarios" / "p1.json").read_text(encoding="utf-8")
    )
    assert [comentario["id"] for comentario in comentarios] == [
        f"c{i}" for i in range(1, 10)
    ]
    assert comentarios[0]["categoria"] == "sugerencia"
    assert comentarios[0]["grupo"] == "G1"
    assert comentarios[1]["narrativa"] is None
    assert comentarios[1]["postura"] is None
