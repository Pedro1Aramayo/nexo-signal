import networkx as nx
import pandas as pd


def construir(senales: dict[str, pd.DataFrame]) -> tuple[nx.Graph, nx.Graph, nx.Graph]:
    temporal = nx.Graph()
    for nombre in ("ec", "ed"):
        for a, b, peso in senales[nombre][["a", "b", "k"]].itertuples(index=False, name=None):
            previo = temporal.get_edge_data(a, b, {}).get("weight", 0)
            temporal.add_edge(a, b, weight=previo + int(peso))

    respuestas = nx.Graph()
    for a, b in senales["er"][["a", "b"]].itertuples(index=False, name=None):
        respuestas.add_edge(a, b)

    union = nx.Graph()
    union.add_edges_from(temporal.edges())
    union.add_edges_from(respuestas.edges())
    return temporal, respuestas, union
