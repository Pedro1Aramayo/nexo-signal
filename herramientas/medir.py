"""Corre un comando y registra tiempo, memoria pico, hardware y almacenamiento en JSON.

Uso:
    python herramientas/medir.py --salida salida/medicion.json --medir-dir salida/practica -- <comando ...>
"""
import argparse
import json
import os
import platform
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def ram_gb() -> float:
    try:
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3, 1)
    except (ValueError, OSError, AttributeError):
        return 0.0


def dir_mb(path: Path) -> float:
    if not path.exists():
        return 0.0
    return round(sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1024**2, 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", type=Path, required=True, help="JSON donde guardar la medición")
    ap.add_argument("--costo", type=Path, help="costo.json que se actualiza con la medición real")
    ap.add_argument("--medir-dir", type=Path, action="append", default=[],
                    help="Directorio cuyo tamaño en disco se registra (repetible)")
    ap.add_argument("comando", nargs=argparse.REMAINDER)
    args = ap.parse_args()
    cmd = args.comando[1:] if args.comando[:1] == ["--"] else args.comando
    if not cmd:
        sys.exit("Falta el comando a medir")

    started = time.time()
    proc = subprocess.run(cmd)
    elapsed = time.time() - started
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    peak_mb = usage.ru_maxrss / 1024 if sys.platform != "darwin" else usage.ru_maxrss / 1024**2

    report = {
        "comando": " ".join(cmd),
        "inicio_utc": datetime.fromtimestamp(started, timezone.utc).isoformat(timespec="seconds"),
        "codigo_salida": proc.returncode,
        "segundos_reloj": round(elapsed, 2),
        "segundos_cpu": round(usage.ru_utime + usage.ru_stime, 2),
        "memoria_pico_mb": round(peak_mb, 1),
        "hardware": {"cpu": cpu_model(), "nucleos": os.cpu_count(), "ram_gb": ram_gb(), "gpu": None,
                     "so": f"{platform.system()} {platform.release()}", "python": platform.python_version()},
        "almacenamiento_mb": {str(p): dir_mb(p) for p in args.medir_dir},
    }
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.costo and proc.returncode == 0 and args.costo.exists():
        costo = json.loads(args.costo.read_text(encoding="utf-8"))
        costo["segundos"] = report["segundos_reloj"]
        hardware = report["hardware"]
        costo["hardware"] = (
            f"{hardware['cpu']}, {hardware['nucleos']} núcleos, "
            f"{hardware['ram_gb']} GB RAM, sin GPU"
        )
        args.costo.write_text(
            json.dumps(costo, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(f"[medir] {elapsed:.1f}s reloj, {report['segundos_cpu']}s CPU, pico {report['memoria_pico_mb']} MB -> {args.salida}")
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
