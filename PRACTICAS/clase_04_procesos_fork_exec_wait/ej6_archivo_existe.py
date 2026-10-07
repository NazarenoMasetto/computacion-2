#!/usr/bin/env python3
"""Ejercicio 6: usar el código de salida del hijo como mensaje (True/False)."""
import os
import sys


def archivo_existe(path):
    """El hijo intenta abrir el archivo: sale con 0 si pudo, 1 si no."""
    pid = os.fork()
    if pid == 0:
        try:
            with open(path):
                pass
            os._exit(0)
        except OSError:
            os._exit(1)
    _, status = os.waitpid(pid, 0)
    return os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


if __name__ == "__main__":
    rutas = sys.argv[1:] or ["/etc/passwd", "/no_existe"]
    for ruta in rutas:
        print(f"{ruta}: {archivo_existe(ruta)}")
