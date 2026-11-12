import math

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
        limite = max(3, math.ceil(0.002 * len(grupo)))
        marcas = candidatos.astype("int64").to_numpy()
        ventana = pd.Timedelta(hours=6).value
        fin = 0
        elegido = None
        for inicio, marca in enumerate(marcas):
            fin = max(fin, inicio)
            while fin < len(marcas) and marcas[fin] <= marca + ventana:
                fin += 1
            if fin - inicio >= limite:
                elegido = pd.Timestamp(marca, tz="UTC").tz_convert("-03:00")
                break
        origenes[narrativa] = elegido.isoformat() if elegido is not None else ""
    return origenes
