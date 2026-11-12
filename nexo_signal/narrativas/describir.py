import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from .origen import _similitudes_cores, fechas_origen


def describir(
    comentarios: pd.DataFrame, vectores: dict[str, np.ndarray]
) -> pd.DataFrame:
    grupos = list(dict.fromkeys(comentarios.loc[comentarios["narrativa"].ne(""), "narrativa"]))
    if not grupos:
        return pd.DataFrame(columns=["narrativa", "titulo", "frases_clave", "fecha_origen"])
    largos = comentarios[~comentarios["respuesta_corta"]]
    documentos = [
        " ".join(largos.loc[largos["narrativa"].eq(narrativa), "core"].dropna())
        for narrativa in grupos
    ]
    frases = {narrativa: [] for narrativa in grupos}
    documentos_validos = [(n, texto) for n, texto in zip(grupos, documentos) if texto.strip()]
    if documentos_validos:
        vectorizador = TfidfVectorizer(
            ngram_range=(1, 2), token_pattern=r"(?u)\b\w+\b", sublinear_tf=True
        )
        try:
            matriz = vectorizador.fit_transform([texto for _, texto in documentos_validos])
            terminos = np.asarray(vectorizador.get_feature_names_out())
            for fila, (narrativa, _) in enumerate(documentos_validos):
                valores = matriz.getrow(fila).toarray().ravel()
                orden = np.lexsort((terminos, -valores))
                frases[narrativa] = [terminos[i] for i in orden if valores[i] > 0][:6]
        except ValueError:
            pass

    origenes = fechas_origen(comentarios, vectores)
    filas = []
    for narrativa in grupos:
        grupo = largos[largos["narrativa"].eq(narrativa)]
        candidatas = grupo.loc[
            grupo["postura"].eq("apoya") & grupo["n_tokens"].ge(5)
        ]
        conteos = candidatas["core"].loc[candidatas["core"].ne("")].value_counts()
        similitudes, _ = _similitudes_cores(candidatas, vectores)
        cores_con_vector = [core for core in conteos.index if core in similitudes]
        titulo = ""
        if cores_con_vector:
            pesos = conteos.reindex(cores_con_vector).to_numpy(dtype=np.int64)
            valores = np.asarray(
                [similitudes[core] for core in cores_con_vector], dtype=np.float64
            )
            orden = np.argsort(valores, kind="stable")
            indice = np.searchsorted(
                np.cumsum(pesos[orden]), 0.8 * pesos.sum(), side="left"
            )
            umbral = valores[orden[min(indice, len(orden) - 1)]]
            centrales = [
                core
                for core in cores_con_vector
                if similitudes[core] >= umbral
            ]
            conteos_centrales = conteos.reindex(centrales)
            maximo = conteos_centrales.max()
            core_titulo = sorted(
                conteos_centrales[conteos_centrales.eq(maximo)].index
            )[0]
            textos = candidatas.loc[
                candidatas["core"].eq(core_titulo), "texto"
            ].fillna("").astype(str).value_counts()
            maximo_texto = textos.max()
            texto = sorted(textos[textos.eq(maximo_texto)].index)[0]
            titulo = " ".join(texto.split())[:140]
        if not cores_con_vector:
            apoya = grupo.loc[grupo["postura"].eq("apoya"), "core"]
            apoya = apoya[apoya.ne("")]
            if len(apoya):
                conteos = apoya.value_counts()
                maximo = conteos.max()
                titulo = sorted(conteos[conteos.eq(maximo)].index)[0]
        filas.append({
            "narrativa": narrativa,
            "titulo": titulo,
            "frases_clave": "|".join(frases[narrativa]),
            "fecha_origen": origenes.get(narrativa, ""),
        })
    return pd.DataFrame(filas)
