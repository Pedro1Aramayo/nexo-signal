import time

import networkx as nx
import numpy as np
import pandas as pd

from . import grafo, senales


def _louvain(red: nx.Graph) -> list[set]:
    nodos = sorted(red.nodes)
    indice = {nodo: posicion for posicion, nodo in enumerate(nodos)}
    canonico = nx.Graph()
    canonico.add_nodes_from(range(len(nodos)))
    canonico.add_weighted_edges_from(sorted(
        (min(indice[a], indice[b]), max(indice[a], indice[b]), datos.get("weight", 1))
        for a, b, datos in red.edges(data=True)
    ))
    return [
        {nodos[posicion] for posicion in comunidad}
        for comunidad in nx.community.louvain_communities(
            canonico, weight="weight", resolution=1, seed=0
        )
    ]


def _candidatos(temporal: nx.Graph, respuestas: nx.Graph) -> list[dict]:
    candidatos = []
    if temporal.number_of_nodes():
        candidatos.extend(
            {"canal": "T", "cuentas": set(comunidad)}
            for comunidad in _louvain(temporal)
            if len(comunidad) >= 4
        )
    if respuestas.number_of_edges():
        truss = nx.k_truss(respuestas, 3)
        if truss.number_of_nodes():
            candidatos.extend(
                {"canal": "R", "cuentas": set(comunidad)}
                for comunidad in _louvain(truss)
                if len(comunidad) >= 4
            )
    return candidatos


def _medir_candidato(candidato: dict, union: nx.Graph, cantidad_aristas: int) -> dict:
    cuentas = candidato["cuentas"]
    n = len(cuentas)
    internas = union.subgraph(cuentas).number_of_edges()
    grados = np.asarray([union.degree[cuenta] for cuenta in cuentas], dtype=float)
    densidad = 2 * internas / (n * (n - 1)) if n > 1 else 0.0
    esperado = (
        (grados.sum() ** 2 - np.square(grados).sum()) / (4 * cantidad_aristas)
        if cantidad_aristas else 0.0
    )
    ratio = internas / esperado if esperado > 0 else (float("inf") if internas else 0.0)
    return {
        **candidato,
        "n_inicial": n,
        "m": internas,
        "densidad": densidad,
        "ratio": ratio,
    }


def _expandir(candidato: dict, union: nx.Graph, respuestas: nx.Graph) -> set:
    cuentas = set(candidato["cuentas"])
    canal = candidato["canal"]
    red = union if canal == "T" else respuestas
    minimo = 3 if canal == "T" else 2
    for _ in range(10):
        vecinos = {}
        for cuenta in cuentas:
            for vecino in red.neighbors(cuenta):
                if vecino not in cuentas:
                    vecinos[vecino] = vecinos.get(vecino, 0) + 1
        nuevos = {
            cuenta for cuenta, cantidad in vecinos.items()
            if cantidad >= minimo and red.degree[cuenta] > 0
            and cantidad / red.degree[cuenta] >= 0.3
        }
        if not nuevos:
            break
        cuentas.update(nuevos)
    return cuentas


def _evidencia(
    miembros: dict[str, set], detalle: dict[str, dict], comentarios: pd.DataFrame,
    cuentas: pd.DataFrame,
) -> pd.DataFrame:
    filas = []
    cuentas_por_id = cuentas.set_index("cuenta_id")
    for grupo, ids in miembros.items():
        comentarios_grupo = comentarios[comentarios["cuenta_id"].isin(ids)]
        creacion = pd.to_datetime(
            cuentas_por_id.reindex(sorted(ids))["fecha_creacion"], errors="coerce", utc=True
        )
        primera = comentarios_grupo.groupby("cuenta_id")["fecha_dt"].min()
        dias = (primera.reindex(sorted(ids)).reset_index(drop=True) - creacion.reset_index(drop=True))
        dias = dias.dt.total_seconds().div(86400).dropna()
        seguidores = pd.to_numeric(
            cuentas_por_id.reindex(sorted(ids))["seguidores"], errors="coerce"
        ).dropna()
        horas = comentarios_grupo["fecha_dt"].dropna().dt.tz_convert("-03:00").dt.hour
        cores = comentarios_grupo.loc[comentarios_grupo["core"].ne(""), "core"].value_counts()
        filas.append({
            "grupo": grupo,
            "n_cuentas": len(ids),
            "canal": detalle[grupo]["canal"],
            "densidad": round(detalle[grupo]["densidad"], 4),
            "ratio": round(detalle[grupo]["ratio"], 2),
            "mediana_dias_cuenta_al_primer_comentario": round(float(dias.median()), 2) if len(dias) else "",
            "mediana_seguidores": round(float(seguidores.median()), 2) if len(seguidores) else "",
            "frac_nocturna": round(float(horas.between(0, 5).mean()), 4) if len(horas) else "",
            "n_publicaciones": int(comentarios_grupo["publicacion_id"].nunique()),
            "ejemplo_texto": cores.index[0] if len(cores) else "",
        })
    return pd.DataFrame(filas, columns=[
        "grupo", "n_cuentas", "canal", "densidad", "ratio",
        "mediana_dias_cuenta_al_primer_comentario", "mediana_seguidores",
        "frac_nocturna", "n_publicaciones", "ejemplo_texto",
    ])


def analizar_coordinacion(
    comentarios: pd.DataFrame, cuentas: pd.DataFrame,
) -> tuple[dict[str, str], pd.DataFrame, dict]:
    tiempos = {}
    inicio = time.perf_counter()
    senales_calculadas, tiempos_senales = senales.calcular_senales(comentarios)
    tiempos.update({f"senales_{nombre}": valor for nombre, valor in tiempos_senales.items()})

    marca = time.perf_counter()
    temporal, respuestas, union = grafo.construir(senales_calculadas)
    tiempos["grafos"] = round(time.perf_counter() - marca, 3)
    marca = time.perf_counter()
    candidatos = [
        _medir_candidato(candidato, union, union.number_of_edges())
        for candidato in _candidatos(temporal, respuestas)
    ]
    aceptados = [
        candidato for candidato in candidatos
        if candidato["densidad"] >= 0.3 and candidato["ratio"] >= 10
    ]
    tiempos["comunidades_y_filtro"] = round(time.perf_counter() - marca, 3)
    marca = time.perf_counter()
    expandidos = [
        {**candidato, "miembros": _expandir(candidato, union, respuestas)}
        for candidato in aceptados
    ]
    propietarios = {}
    for indice, candidato in enumerate(expandidos):
        for cuenta in candidato["miembros"]:
            actual = propietarios.get(cuenta)
            if actual is None or candidato["ratio"] > expandidos[actual]["ratio"]:
                propietarios[cuenta] = indice
    miembros_por_indice = {
        indice: {cuenta for cuenta, propietario in propietarios.items() if propietario == indice}
        for indice in range(len(expandidos))
    }
    miembros_por_indice = {
        indice: miembros
        for indice, miembros in miembros_por_indice.items()
        if len(miembros) >= 3
    }
    orden = sorted(
        miembros_por_indice,
        key=lambda indice: (
            -len(miembros_por_indice[indice]),
            expandidos[indice]["canal"],
            -expandidos[indice]["ratio"],
        ),
    )
    grupos, detalle = {}, {}
    for numero, indice in enumerate(orden, 1):
        grupo = f"G{numero}"
        grupo_miembros = miembros_por_indice[indice]
        grupos.update({cuenta: grupo for cuenta in grupo_miembros})
        detalle[grupo] = expandidos[indice]
        detalle[grupo]["miembros_finales"] = grupo_miembros
    evidencia = _evidencia(
        {grupo: datos["miembros_finales"] for grupo, datos in detalle.items()},
        detalle, comentarios, cuentas,
    )
    tiempos["expansion_y_evidencia"] = round(time.perf_counter() - marca, 3)
    tiempos["total"] = round(time.perf_counter() - inicio, 3)
    resumen = {
        "senales": {nombre: len(df) for nombre, df in senales_calculadas.items()},
        "candidatos": len(candidatos),
        "candidatos_aceptados": len(aceptados),
        "cuentas_coordinadas": len(grupos),
        "grupos": len(set(grupos.values())),
        "segundos_por_paso": tiempos,
    }
    return grupos, evidencia, resumen


def detectar_coordinacion(comentarios: pd.DataFrame, cuentas: pd.DataFrame) -> dict[str, str]:
    grupos, _, _ = analizar_coordinacion(comentarios, cuentas)
    return grupos
