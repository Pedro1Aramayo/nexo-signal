import resource
import sys


def memoria_pico_mb() -> float:
    uso = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(uso / 1024 if sys.platform != "darwin" else uso / 1024**2, 1)
