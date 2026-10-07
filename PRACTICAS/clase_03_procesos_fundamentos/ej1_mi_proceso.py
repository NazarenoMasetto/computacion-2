#!/usr/bin/env python3
"""Ejercicio 1: explorar mi propio proceso usando os y /proc.

Muestra PID, PPID, directorio de trabajo, file descriptors abiertos
y las primeras líneas del mapa de memoria virtual.
Uso: python3 ej1_mi_proceso.py [cantidad_de_lineas_de_maps]
"""

import os
import sys


def main():
    lineas = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    pid = os.getpid()

    print(f"PID:  {pid}")
    print(f"PPID: {os.getppid()}")
    print(f"CWD:  {os.getcwd()}")

    # Abrimos un archivo a propósito para verlo aparecer en la tabla de fds
    extra = open(__file__)

    print("\nFile descriptors abiertos:")
    ruta_fd = f"/proc/{pid}/fd"
    for fd in sorted(os.listdir(ruta_fd), key=int):
        try:
            destino = os.readlink(f"{ruta_fd}/{fd}")
            print(f"  fd {fd:>3} -> {destino}")
        except OSError:
            # el fd que usó listdir para leer el directorio ya se cerró
            pass

    print(f"\nMapa de memoria (primeras {lineas} líneas):")
    print("  rango de direcciones          perms offset   dev   inodo   ruta")
    with open(f"/proc/{pid}/maps") as f:
        for i, linea in enumerate(f):
            if i >= lineas:
                break
            print(f"  {linea.rstrip()}")

    extra.close()


if __name__ == "__main__":
    main()
