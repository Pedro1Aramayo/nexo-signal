import argparse
from pathlib import Path

import pandas as pd


def diagnosticar(datos: Path, entrega: Path) -> None:
    verdad = pd.read_csv(datos / "verdad" / "comentarios.csv.gz", dtype=str, keep_default_na=False)
    predichos = pd.read_csv(entrega / "comentarios.csv", dtype=str, keep_default_na=False)
    columna_narrativa = "narrativa_id" if "narrativa_id" in verdad else "narrativa"
    columna_postura = "postura" if "postura" in verdad else "stance"
    verdad = verdad[["comentario_id", columna_narrativa, columna_postura]].rename(columns={
        columna_narrativa: "verdad_narrativa",
        columna_postura: "verdad_postura",
    })
    tabla = verdad.merge(
        predichos[["comentario_id", "narrativa", "postura"]],
        on="comentario_id", how="inner",
    )
    ruido_real = tabla["verdad_narrativa"].isin(("", "ninguna", "none"))
    ruido_predicho = tabla["narrativa"].isin(("", "ninguna"))
    tp = int((ruido_real & ruido_predicho).sum())
    fp = int((~ruido_real & ruido_predicho).sum())
    fn = int((ruido_real & ~ruido_predicho).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    narrativas_reales = sorted(set(tabla.loc[~ruido_real, "verdad_narrativa"]))
    print("Narrativa real | Mejor cluster | Purity | Comentarios")
    for narrativa in narrativas_reales:
        filas = tabla[tabla["verdad_narrativa"].eq(narrativa)]
        asignadas = filas[~filas["narrativa"].isin(("", "ninguna"))]
        if asignadas.empty:
            cluster, pureza = "sin asignar", 0.0
        else:
            conteos = asignadas["narrativa"].value_counts()
            cluster = sorted(conteos[conteos.eq(conteos.max())].index)[0]
            pureza = float(conteos.max() / len(asignadas))
        print(f"{narrativa} | {cluster} | {pureza:.3f} | {len(filas)}")

    print("\nCluster | Narrativa dominante | Exactitud postura | Orientación invertida")
    asignadas = tabla[~tabla["narrativa"].isin(("", "ninguna")) & ~ruido_real]
    for cluster, filas in asignadas.groupby("narrativa", sort=True):
        dominante = filas["verdad_narrativa"].value_counts().index[0]
        subset = filas[filas["verdad_narrativa"].eq(dominante)]
        valida = subset["verdad_postura"].isin(("apoya", "rechaza"))
        subset = subset[valida]
        if subset.empty:
            exactitud, invertida = 0.0, False
        else:
            exactitud = float((subset["postura"] == subset["verdad_postura"]).mean())
            opuesta = subset["verdad_postura"].map({"apoya": "rechaza", "rechaza": "apoya"})
            invertida = float((subset["postura"] == opuesta).mean()) > exactitud
        print(f"{cluster} | {dominante} | {exactitud:.3f} | {'sí' if invertida else 'no'}")

    print(
        f"\nRuido: TP={tp} FP={fp} FN={fn} | "
        f"precision={precision:.3f} recall={recall:.3f} F1={f1:.3f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnóstico separado contra la verdad de práctica.")
    parser.add_argument("--datos", type=Path, default=Path("datos/practica"))
    parser.add_argument("--entrega", type=Path, default=Path("salida/practica_nexo"))
    args = parser.parse_args()
    diagnosticar(args.datos, args.entrega)


if __name__ == "__main__":
    main()
