import os
import platform
import sys
from pathlib import Path


MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def cpu() -> str:
    try:
        for linea in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if linea.startswith("model name"):
                return linea.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def ram_gb() -> float:
    try:
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3, 1)
    except (AttributeError, OSError, ValueError):
        return 0.0


def hardware() -> str:
    return (
        f"{cpu()}, {os.cpu_count() or 1} núcleos, {ram_gb()} GB RAM, sin GPU"
    )


def generar_costo(comentarios: int, segundos: float) -> dict:
    return {
        "comentarios_procesados": int(comentarios),
        "segundos": round(float(segundos), 1),
        "tokens_ia": 0,
        "usd_ia": 0,
        "usd_por_mil_comentarios": 0,
        "hardware": hardware(),
        "almacenamiento": "DuckDB + Parquet local",
        "notas": f"{MODELO}; embeddings locales en CPU, sin IA generativa",
    }
