from nexo_signal.texto.normalizar import normalizar, normalizar_corpus


def test_normaliza_acentos_repeticiones_y_menciones():
    assert normalizar("Árboool @Cuenta https://ejemplo.com/a") == "arbol"


def test_aprende_y_quita_filler_de_borde():
    textos = [f"Bueno, la obra avanza etapa{i}" for i in range(300)]
    corpus = normalizar_corpus(textos)
    assert corpus.loc[0, "core"] == "la obra avanza etapa0"
    assert corpus.loc[0, "n_tokens"] == 5
