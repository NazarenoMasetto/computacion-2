#!/usr/bin/env python3
"""Adicional: watcher de archivos. Un hijo hace polling del mtime de un archivo
y avisa cada vez que cambia; el padre lo mata con SIGTERM después de N segundos.

Uso: python3 adicional_watcher.py ARCHIVO [segundos]
"""
import os
import signal
import sys
import time


def vigilar(path, intervalo=0.2):
    """Loop del hijo: compara el mtime contra el último visto."""
    ultimo = os.stat(path).st_mtime_ns if os.path.exists(path) else None
    print(f"[watcher {os.getpid()}] vigilando {path}", flush=True)
    while True:
        actual = os.stat(path).st_mtime_ns if os.path.exists(path) else None
        if actual != ultimo:
            if actual is None:
                print(f"[watcher] {path} fue borrado", flush=True)
            else:
                print(f"[watcher] {path} modificado a las {time.strftime('%H:%M:%S')}", flush=True)
            ultimo = actual
        time.sleep(intervalo)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    duracion = float(sys.argv[2]) if len(sys.argv) > 2 else 10

    pid = os.fork()
    if pid == 0:
        try:
            vigilar(path)
        finally:
            os._exit(0)

    # Padre: deja trabajar al watcher y después lo termina con una señal
    time.sleep(duracion)
    os.kill(pid, signal.SIGTERM)
    _, status = os.waitpid(pid, 0)
    if os.WIFSIGNALED(status):
        print(f"[padre] watcher terminado por señal {os.WTERMSIG(status)} (SIGTERM)")


if __name__ == "__main__":
    main()
