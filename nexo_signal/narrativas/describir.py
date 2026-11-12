import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from .origen import fechas_origen


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
        apoya = grupo.loc[grupo["postura"].eq("apoya"), "core"]
        apoya = apoya[apoya.ne("")]
        if len(apoya):
            conteos = apoya.value_counts()
            maximo = conteos.max()
            titulo = sorted(conteos[conteos.eq(maximo)].index)[0]
        else:
            titulo = ""
        filas.append({
            "narrativa": narrativa,
            "titulo": titulo,
            "frases_clave": "|".join(frases[narrativa]),
            "fecha_origen": origenes.get(narrativa, ""),
        })
    return pd.DataFrame(filas)
