from collections import defaultdict

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors


RESOLUCION_LOUVAIN = 0.1


def agrupar(comentarios: pd.DataFrame, vectores: dict[str, np.ndarray]) -> dict[str, int]:
    cores = list(dict.fromkeys(core for core in comentarios["core"] if core))
    if not cores:
        return {}
    matriz = np.vstack([vectores[core] for core in cores]).astype(np.float32)
    grafo = nx.Graph()
    grafo.add_nodes_from(range(len(cores)))
    if len(cores) > 1:
        vecinos = NearestNeighbors(
            n_neighbors=min(11, len(cores)), metric="cosine"
        ).fit(matriz)
        distancias, indices = vecinos.kneighbors(matriz)
        for i, (fila_dist, fila_idx) in enumerate(zip(distancias, indices)):
            for distancia, j in zip(fila_dist, fila_idx):
                similitud = 1.0 - float(distancia)
                if i != j and similitud >= 0.6:
                    previo = grafo.get_edge_data(i, j, {}).get("weight", 0.0)
                    grafo.add_edge(i, j, weight=max(previo, similitud))

    posiciones = {core: i for i, core in enumerate(cores)}
    por_id = comentarios.set_index("comentario_id")["core"].to_dict()
    respuestas = defaultdict(int)
    for fila in comentarios.itertuples(index=False):
        if not fila.respuesta_a or fila.n_tokens <= 3:
            continue
        padre = por_id.get(fila.respuesta_a, "")
        if fila.core and padre and fila.core != padre:
            respuestas[(fila.core, padre)] += 1
    for (core, padre), cuenta in respuestas.items():
        a, b = posiciones[core], posiciones[padre]
        peso = grafo.get_edge_data(a, b, {}).get("weight", 0.0)
        grafo.add_edge(a, b, weight=peso + 0.5 * min(cuenta, 5))

    comunidades = nx.community.louvain_communities(
        grafo, weight="weight", resolution=RESOLUCION_LOUVAIN, seed=0
    )
    etiquetas = {
        nodo: grupo
        for grupo, comunidad in enumerate(comunidades)
        for nodo in comunidad
    }
    return {core: etiquetas[i] for i, core in enumerate(cores)}
