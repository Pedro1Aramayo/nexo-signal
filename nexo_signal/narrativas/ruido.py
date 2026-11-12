import pandas as pd
from scipy.stats import binom


def asignar(comentarios: pd.DataFrame, clusters: dict[str, int]) -> tuple[pd.DataFrame, dict[int, str]]:
    df = comentarios.copy()
    df["cluster_id"] = df["core"].map(clusters).fillna(-1).astype(int)
    ids = set(df["comentario_id"])
    df["respuesta_corta"] = (
        df["respuesta_a"].ne("") & df["respuesta_a"].isin(ids) & df["n_tokens"].le(3)
    )
    respuestas = set(df.loc[df["respuesta_a"].ne(""), "respuesta_a"])
    df["engaged"] = df["respuesta_a"].ne("") | df["comentario_id"].isin(respuestas)
    evaluables = df[~df["respuesta_corta"]]
    p0 = float(evaluables["engaged"].mean()) if len(evaluables) else 0.0

    ruido_cores = set()
    por_core = evaluables[evaluables["cluster_id"].ge(0)].groupby("core")["engaged"].agg(
        n="size", k="sum"
    )
    for core, fila in por_core.iterrows():
        n, k = int(fila["n"]), int(fila["k"])
        if n * p0 >= 5 and binom.cdf(k, n, p0) < 1e-3:
            ruido_cores.add(core)

    actividad = evaluables[
        evaluables["cluster_id"].ge(0) & ~evaluables["core"].isin(ruido_cores)
    ].groupby("cluster_id")["engaged"].agg(n="size", k="sum")
    ruido_clusters = {
        int(cluster)
        for cluster, fila in actividad.iterrows()
        if int(fila["n"]) >= 30 and fila["k"] / fila["n"] < 0.25 * p0
    }

    df["narrativa"] = ""
    asignados = (
        df["cluster_id"].ge(0) & ~df["core"].isin(ruido_cores) & df["fecha_dt"].notna()
    )
    asignados &= ~df["cluster_id"].isin(ruido_clusters)
    tamanos = df.loc[asignados].groupby("cluster_id").size().to_dict()
    ordenados = sorted(tamanos, key=lambda cluster: (-tamanos[cluster], cluster))
    etiqueta_cluster = {cluster: f"n{i:02d}" for i, cluster in enumerate(ordenados, 1)}
    df.loc[asignados, "narrativa"] = df.loc[asignados, "cluster_id"].map(etiqueta_cluster)

    etiquetas = df["narrativa"].tolist()
    posiciones = {comentario_id: i for i, comentario_id in enumerate(df["comentario_id"])}
    padres = df["respuesta_a"].tolist()
    cortas = df["respuesta_corta"].tolist()
    resueltas = [not es_corta for es_corta in cortas]
    visitando = set()

    def resolver(i: int) -> str:
        if resueltas[i]:
            return etiquetas[i]
        comentario_id = df.iloc[i]["comentario_id"]
        if comentario_id in visitando:
            resueltas[i] = True
            etiquetas[i] = ""
            return ""
        visitando.add(comentario_id)
        padre = padres[i]
        if pd.notna(df.iloc[i]["fecha_dt"]) and padre in posiciones:
            etiquetas[i] = resolver(posiciones[padre])
        resueltas[i] = True
        visitando.discard(comentario_id)
        return etiquetas[i]

    for i, es_corta in enumerate(cortas):
        if es_corta:
            resolver(i)
    df["narrativa"] = etiquetas
    return df, etiqueta_cluster
