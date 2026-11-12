import re
import unicodedata
from collections import Counter, defaultdict
from typing import Iterable

import pandas as pd


SEPARADORES = {",", ".", ":", ";", "!", "?"}


def normalizar(texto: object) -> str:
    texto = "" if pd.isna(texto) else str(texto)
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"https?://\S+|@\w+", " ", texto)
    texto = re.sub(r"(\w)\1{2,}", r"\1", texto)
    texto = re.sub(r"[^\w\s#,.:;!?]", " ", texto)
    texto = re.sub(r"([,.:;!?])", r" \1 ", texto)
    return " ".join(texto.split())


def _segmentos(texto: str) -> list[str]:
    segmentos = []
    actual = []
    for token in texto.split():
        if token in SEPARADORES:
            if actual:
                segmentos.append(" ".join(actual))
                actual = []
        else:
            actual.append(token)
    if actual:
        segmentos.append(" ".join(actual))
    return segmentos


def _aprender_bordes(segmentos: list[list[str]], cantidad: int) -> tuple[set[str], set[str]]:
    conteo_inicio, resto_inicio = Counter(), defaultdict(set)
    conteo_fin, resto_fin = Counter(), defaultdict(set)
    for partes in segmentos:
        if len(partes) < 2:
            continue
        conteo_inicio[partes[0]] += 1
        resto_inicio[partes[0]].add(" ".join(partes[1:]))
        conteo_fin[partes[-1]] += 1
        resto_fin[partes[-1]].add(" ".join(partes[:-1]))

    umbral = cantidad * 0.002
    inicio = {
        texto for texto, cuenta in conteo_inicio.items()
        if cuenta >= umbral and len(texto.split()) <= 4
        and len(resto_inicio[texto]) / cuenta >= 0.3
    }
    fin = {
        texto for texto, cuenta in conteo_fin.items()
        if cuenta >= umbral and len(texto.split()) <= 4
        and len(resto_fin[texto]) / cuenta >= 0.3
    }
    return inicio, fin


def _extraer_core(partes: list[str], inicio: set[str], fin: set[str]) -> str:
    partes = list(partes)
    while len(partes) > 1 and partes[0] in inicio:
        partes.pop(0)
    while len(partes) > 1 and partes[-1] in fin:
        partes.pop()
    return " ".join(partes)


def normalizar_corpus(textos: Iterable[object]) -> pd.DataFrame:
    normalizados = [normalizar(texto) for texto in textos]
    segmentos = [_segmentos(texto) for texto in normalizados]
    inicio, fin = _aprender_bordes(segmentos, len(normalizados))
    cores = [_extraer_core(partes, inicio, fin) for partes in segmentos]
    return pd.DataFrame({
        "normalizado": normalizados,
        "core": cores,
        "n_tokens": [len(re.findall(r"\w+", texto)) for texto in normalizados],
    })
