import re

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import eigsh
from sklearn.neighbors import NearestNeighbors


DESACUERDOS = (
    "mentira", "falso", "nada que ver", "no es asi", "cualquiera",
    "verso", "fake", "para nada", "no",
)
REFUTACION = re.compile(
    r"\b(falso|mentira|mentiras|prueba|pruebas|informarse|informate|informense|"
    r"nadie|chequea\w*|fuente|fuentes|dato|datos|realidad|cierto|verso|invento|"
    r"fake|desinformacion|pero|no es|dejen de|chamuyo|operacion|exagera\w*)\b"
)


def _contradice(texto: str) -> bool:
    return any(
        re.search(rf"(?<!\w){re.escape(frase)}(?!\w)", texto)
        for frase in DESACUERDOS
    )


def _vector_firmado(
    cores: list[str], vectores: dict[str, np.ndarray], respuestas: dict[tuple[str, str], int]
) -> np.ndarray:
    n = len(cores)
    if n == 1:
        return np.ones(1)
    matriz = np.vstack([vectores[core] for core in cores]).astype(np.float32)
    vecinos = NearestNeighbors(n_neighbors=min(11, n), metric="cosine").fit(matriz)
    distancias, indices = vecinos.kneighbors(matriz)
    posiciones = {core: i for i, core in enumerate(cores)}
    pesos = {}
    for i, (fila_dist, fila_idx) in enumerate(zip(distancias, indices)):
        for distancia, j in zip(fila_dist, fila_idx):
            similitud = 1.0 - float(distancia)
            if i != j and similitud >= 0.6:
                a, b = min(i, j), max(i, j)
                pesos[(a, b)] = max(pesos.get((a, b), 0.0), similitud)
    for (core, padre), cuenta in respuestas.items():
        if core in posiciones and padre in posiciones and core != padre:
            a, b = sorted((posiciones[core], posiciones[padre]))
            pesos[(a, b)] = pesos.get((a, b), 0.0) - cuenta

    filas, columnas, valores = [], [], []
    for (a, b), peso in pesos.items():
        filas.extend((a, b))
        columnas.extend((b, a))
        valores.extend((peso, peso))
    grafo = coo_matrix((valores, (filas, columnas)), shape=(n, n)).tocsr()
    if n <= 2:
        vector = np.linalg.eigh(grafo.toarray())[1][:, -1]
    else:
        inicio = np.arange(1, n + 1, dtype=np.float64)
        inicio /= np.linalg.norm(inicio)
        vector = eigsh(grafo, k=1, which="LA", v0=inicio, return_eigenvectors=True)[1][:, 0]
    lados = np.sign(vector).astype(int)
    lados[vector == 0] = 0
    ceros = np.flatnonzero(lados == 0)
    con_lado = np.flatnonzero(lados != 0)
    if len(ceros) and len(con_lado):
        vecinos_lado = NearestNeighbors(n_neighbors=1, metric="cosine").fit(matriz[con_lado])
        for i in ceros:
            vecino = vecinos_lado.kneighbors(matriz[i:i + 1], return_distance=False)[0, 0]
            lados[i] = lados[con_lado[vecino]]
    lados[lados == 0] = 1
    return lados


def asignar_posturas(
    comentarios: pd.DataFrame, vectores: dict[str, np.ndarray]
) -> tuple[pd.DataFrame, dict[str, dict]]:
    df = comentarios.copy()
    df["postura"] = ""
    por_id = df.set_index("comentario_id")["core"].to_dict()
    respuestas: dict[str, dict[tuple[str, str], int]] = {}
    for fila in df.itertuples(index=False):
        if fila.narrativa and fila.narrativa != "ninguna" and fila.respuesta_a and fila.n_tokens > 3:
            padre = por_id.get(fila.respuesta_a, "")
            if padre and padre != fila.core:
                clave = (fila.core, padre)
                tabla = respuestas.setdefault(fila.narrativa, {})
                tabla[clave] = tabla.get(clave, 0) + 1

    lados_por_core = {}
    orientaciones = {}
    grupo_largos = df[df["narrativa"].ne("") & ~df["respuesta_corta"]]
    for narrativa, grupo in grupo_largos.groupby("narrativa", sort=False):
        cores = list(dict.fromkeys(core for core in grupo["core"] if core))
        if not cores:
            continue
        lados = _vector_firmado(cores, vectores, respuestas.get(narrativa, {}))
        indices = dict(zip(cores, lados))
        tasas = {}
        for lado in (-1, 1):
            filas_lado = grupo[grupo["core"].map(indices).eq(lado)]
            hits = int(filas_lado["normalizado"].map(
                lambda texto: bool(REFUTACION.search(texto))
            ).sum())
            tasas[lado] = (hits + 1) / (len(filas_lado) + 2)
        if tasas[-1] > tasas[1]:
            lado_rechaza = -1
            regla = "lexico"
        elif tasas[1] > tasas[-1]:
            lado_rechaza = 1
            regla = "lexico"
        else:
            tiempos = {}
            for lado in (-1, 1):
                valores = grupo.loc[
                    grupo["core"].map(indices).eq(lado), "fecha_dt"
                ].dropna()
                if len(valores):
                    tiempos[lado] = valores.astype("int64").to_numpy()
            if len(tiempos) == 2:
                cuantiles = {
                    lado: np.quantile(valores, 0.02) for lado, valores in tiempos.items()
                }
                lado_apoya = min(cuantiles, key=lambda lado: (cuantiles[lado], -lado))
            else:
                lado_apoya = next(iter(tiempos), 1)
            lado_rechaza = -lado_apoya
            regla = "tiempo"
        orientaciones[narrativa] = {
            "rate_lado_a": round(float(tasas[-1]), 6),
            "rate_lado_b": round(float(tasas[1]), 6),
            "regla": regla,
        }
        lados_por_core.update({
            (narrativa, core): "rechaza" if lado == lado_rechaza else "apoya"
            for core, lado in indices.items()
        })

    for i, fila in enumerate(df.itertuples(index=False)):
        if fila.narrativa:
            df.iat[i, df.columns.get_loc("postura")] = lados_por_core.get(
                (fila.narrativa, fila.core), ""
            )

    posiciones = {comentario_id: i for i, comentario_id in enumerate(df["comentario_id"])}
    visitando = set()
    resueltas = [not fila.respuesta_corta for fila in df.itertuples(index=False)]
    posturas = df["postura"].tolist()

    def heredar(i: int) -> str:
        if resueltas[i]:
            return posturas[i]
        comentario_id = df.iloc[i]["comentario_id"]
        if comentario_id in visitando:
            resueltas[i] = True
            return ""
        visitando.add(comentario_id)
        padre = fila_por_id.get(df.iloc[i]["respuesta_a"])
        if padre is not None:
            posturas[i] = heredar(padre)
            if posturas[i] and _contradice(df.iloc[i]["normalizado"]):
                posturas[i] = "rechaza" if posturas[i] == "apoya" else "apoya"
        resueltas[i] = True
        visitando.discard(comentario_id)
        return posturas[i]

    fila_por_id = {comentario_id: i for i, comentario_id in enumerate(df["comentario_id"])}
    for i, fila in enumerate(df.itertuples(index=False)):
        if fila.respuesta_corta:
            heredar(i)
    df["postura"] = posturas
    return df, orientaciones
