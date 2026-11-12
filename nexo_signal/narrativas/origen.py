import numpy as np

import pandas as pd


def _similitudes_cores(grupo: pd.DataFrame, vectores: dict[str, np.ndarray]):
    conteos = grupo["core"].value_counts()
    cores = []
    pesos = []
    matrices = []
    for core, peso in conteos.items():
        if not core or core not in vectores:
            continue
        vector = np.asarray(vectores[core], dtype=np.float64)
        norma = np.linalg.norm(vector)
        if not np.isfinite(norma) or norma == 0:
            continue
        cores.append(core)
        pesos.append(int(peso))
        matrices.append(vector / norma)
    if not cores:
        return {}, None

    matriz = np.vstack(matrices)
    pesos = np.asarray(pesos, dtype=np.int64)
    centro = np.average(matriz, axis=0, weights=pesos)
    norma_centro = np.linalg.norm(centro)
    if not np.isfinite(norma_centro) or norma_centro == 0:
        return {}, None
    similitudes = matriz @ (centro / norma_centro)
    orden = np.argsort(similitudes, kind="stable")
    indice_mediana = np.searchsorted(
        np.cumsum(pesos[orden]), pesos.sum() / 2, side="left"
    )
    return dict(zip(cores, similitudes)), float(similitudes[orden[indice_mediana]])


def _origen_por_ventana(candidatos: pd.Series) -> str:
    marcas = candidatos.astype("int64").to_numpy()
    ventana = pd.Timedelta(hours=6).value
    indices_fin = np.searchsorted(marcas, marcas + ventana, side="left")
    cantidades = indices_fin - np.arange(len(marcas))
    pico = int(cantidades.max())
    candidatas = np.flatnonzero(cantidades >= max(3, 0.1 * pico))
    indice = int(candidatas[0]) if len(candidatas) else 0
    elegido = pd.Timestamp(int(marcas[indice]), unit="ns", tz="UTC").tz_convert("-03:00")
    return elegido.isoformat()


def fechas_origen(
    comentarios: pd.DataFrame, vectores: dict[str, np.ndarray]
) -> dict[str, str]:
    origenes = {}
    for narrativa, grupo in comentarios[comentarios["narrativa"].ne("")].groupby(
        "narrativa", sort=False
    ):
        no_cortos = grupo.loc[~grupo["respuesta_corta"]]
        candidatos = no_cortos.loc[no_cortos["fecha_dt"].notna()]
        if candidatos.empty:
            origenes[narrativa] = ""
            continue
        similitudes, mediana = _similitudes_cores(grupo, vectores)
        if mediana is not None:
            centrales = candidatos.loc[
                candidatos["core"].map(similitudes).ge(mediana)
            ]
        else:
            centrales = candidatos.iloc[0:0]
        if len(centrales) < 3:
            centrales = candidatos
        origenes[narrativa] = _origen_por_ventana(
            centrales["fecha_dt"].sort_values()
        )
    return origenes
