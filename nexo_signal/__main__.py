import argparse
import json
import time
from pathlib import Path

from nexo_signal.coordinacion.comunidades import analizar_coordinacion
from nexo_signal.ingesta.cargar import cargar
from nexo_signal.narrativas.agrupar import agrupar
from nexo_signal.narrativas.describir import describir
from nexo_signal.narrativas.postura import asignar_posturas
from nexo_signal.narrativas.ruido import asignar
from nexo_signal.reporte.costo import generar_costo
from nexo_signal.reporte.metricas import memoria_pico_mb
from nexo_signal.texto import embeddings
from nexo_signal.texto.normalizar import normalizar_corpus


def ejecutar(datos: Path, entrega: Path, cache: Path) -> dict:
    inicio_total = time.perf_counter()
    etapas = {}
    entrega.mkdir(parents=True, exist_ok=True)
    cache_corrida = cache / datos.name
    cache_corrida.mkdir(parents=True, exist_ok=True)

    inicio = time.perf_counter()
    tablas = cargar(datos, cache_corrida)
    comentarios = tablas["comentarios"]
    etapas["ingesta"] = round(time.perf_counter() - inicio, 3)

    inicio = time.perf_counter()
    textos = normalizar_corpus(comentarios["texto"])
    for columna in textos:
        comentarios[columna] = textos[columna].to_numpy()
    comentarios.to_parquet(cache_corrida / "comentarios_texto.parquet", index=False)
    etapas["normalizacion"] = round(time.perf_counter() - inicio, 3)

    inicio = time.perf_counter()
    vectores = embeddings.calcular_embeddings(
        comentarios["core"].drop_duplicates().tolist(), cache_corrida / "embeddings"
    )
    etapas["embeddings"] = round(time.perf_counter() - inicio, 3)

    inicio = time.perf_counter()
    clusters = agrupar(comentarios, vectores)
    comentarios, _ = asignar(comentarios, clusters)
    comentarios, orientaciones_postura = asignar_posturas(comentarios, vectores)
    narrativas = describir(comentarios, vectores)
    etapas["narrativas"] = round(time.perf_counter() - inicio, 3)

    inicio = time.perf_counter()
    grupos, evidencia, coordinacion = analizar_coordinacion(comentarios, tablas["cuentas"])
    evidencia.to_csv(entrega / "grupos_coordinados.csv", index=False)
    cuentas = tablas["cuentas"][["cuenta_id"]].copy()
    cuentas["grupo"] = cuentas["cuenta_id"].map(grupos).fillna("")
    etapas["coordinacion"] = round(time.perf_counter() - inicio, 3)
    etapas["coordinacion_pasos"] = coordinacion["segundos_por_paso"]

    inicio = time.perf_counter()
    comentarios[["comentario_id", "narrativa", "postura"]].to_csv(
        entrega / "comentarios.csv", index=False
    )
    narrativas.to_csv(entrega / "narrativas.csv", index=False)
    cuentas.to_csv(entrega / "cuentas.csv", index=False)
    etapas["escritura"] = round(time.perf_counter() - inicio, 3)

    costo = generar_costo(len(comentarios), time.perf_counter() - inicio_total)
    (entrega / "costo.json").write_text(
        json.dumps(costo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    metricas = {
        "segundos_por_etapa": etapas,
        "segundos_total": round(time.perf_counter() - inicio_total, 3),
        "memoria_pico_mb": memoria_pico_mb(),
        "conteos": {
            "comentarios": int(len(comentarios)),
            "cuentas": int(len(cuentas)),
            "cores_unicos_no_vacios": int(comentarios.loc[comentarios["core"].ne(""), "core"].nunique()),
            "narrativas": int(narrativas.shape[0]),
            "comentarios_ruido": int(comentarios["narrativa"].eq("").sum()),
            "grupos_coordinados": int(len(set(grupos.values()))),
            "cuentas_coordinadas": int(len(grupos)),
            "clusters_louvain": int(len(set(clusters.values()))),
        },
        "orientacion_postura": orientaciones_postura,
        "coordinacion": coordinacion,
    }
    (entrega / "metricas.json").write_text(
        json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"Listo: {len(comentarios)} comentarios, {len(narrativas)} narrativas, "
        f"{len(set(grupos.values()))} grupos coordinados."
    )
    return metricas


def main() -> None:
    parser = argparse.ArgumentParser(description="Detecta narrativas y coordinación en comentarios.")
    parser.add_argument("--datos", type=Path, required=True)
    parser.add_argument("--entrega", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path(".cache"))
    args = parser.parse_args()
    ejecutar(args.datos, args.entrega, args.cache)


if __name__ == "__main__":
    main()
