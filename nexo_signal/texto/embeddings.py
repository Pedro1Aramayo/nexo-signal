import hashlib
import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer


MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def clave(core: str) -> str:
    return hashlib.sha1(f"{MODELO}\0{core}".encode("utf-8")).hexdigest()


def calcular_embeddings(cores: list[str], cache: Path) -> dict[str, np.ndarray]:
    unicos = list(dict.fromkeys(core for core in cores if core))
    if not unicos:
        return {}
    cache.mkdir(parents=True, exist_ok=True)
    archivo = cache / "embeddings.parquet"
    existentes = {}
    if archivo.exists():
        tabla = pd.read_parquet(archivo)
        existentes = {
            fila.clave: np.asarray(fila.vector, dtype=np.float32)
            for fila in tabla.itertuples(index=False)
        }
    faltantes = [core for core in unicos if clave(core) not in existentes]
    if faltantes:
        torch.set_num_threads(max(1, os.cpu_count() or 1))
        modelo = SentenceTransformer(MODELO, device="cpu")
        vectores = modelo.encode(
            faltantes, batch_size=128, normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=len(faltantes) > 512,
        )
        existentes.update({
            clave(core): np.asarray(vector, dtype=np.float32)
            for core, vector in zip(faltantes, vectores)
        })
        pd.DataFrame({
            "clave": [clave(core) for core in unicos],
            "core": unicos,
            "vector": [existentes[clave(core)].tolist() for core in unicos],
        }).to_parquet(archivo, index=False)
    return {core: existentes[clave(core)] for core in unicos}
