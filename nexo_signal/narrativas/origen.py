import numpy as np

import pandas as pd


def fechas_origen(comentarios: pd.DataFrame) -> dict[str, str]:
    origenes = {}
    for narrativa, grupo in comentarios[comentarios["narrativa"].ne("")].groupby(
        "narrativa", sort=False
    ):
        candidatos = grupo.loc[~grupo["respuesta_corta"], "fecha_dt"].dropna().sort_values()
        if candidatos.empty:
            origenes[narrativa] = ""
            continue
        marcas = candidatos.astype("int64").to_numpy()
        ventana = pd.Timedelta(hours=6).value
        indices_fin = np.searchsorted(marcas, marcas + ventana, side="left")
        cantidades = indices_fin - np.arange(len(marcas))
        pico = int(cantidades.max())
        candidatas = np.flatnonzero(cantidades >= max(3, 0.1 * pico))
        indice = int(candidatas[0]) if len(candidatas) else 0
        elegido = pd.Timestamp(int(marcas[indice]), unit="ns", tz="UTC").tz_convert("-03:00")
        origenes[narrativa] = elegido.isoformat()
    return origenes
