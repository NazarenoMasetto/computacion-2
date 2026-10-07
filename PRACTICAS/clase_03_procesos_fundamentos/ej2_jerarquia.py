#!/usr/bin/env python3
"""Ejercicio 2 (complemento): subir la jerarquía de procesos hasta el PID 1.

Arranca en un PID (por defecto, el proceso padre de este script, o sea
la shell que lo lanzó) y va leyendo el PPID en /proc/<pid>/stat hasta
llegar a init/systemd.
Uso: python3 ej2_jerarquia.py [pid]
"""

import os
import sys


def leer_stat(pid):
    """Devuelve (nombre, ppid) leyendo /proc/<pid>/stat.

    El nombre va entre paréntesis y puede tener espacios, por eso se
    corta en el último ')'.
    """
    with open(f"/proc/{pid}/stat") as f:
        datos = f.read()
    nombre = datos[datos.index("(") + 1:datos.rindex(")")]
    resto = datos[datos.rindex(")") + 2:].split()
    ppid = int(resto[1])  # resto[0] es el estado, resto[1] el PPID
    return nombre, ppid


def leer_cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().replace(b"\0", b" ").decode(errors="replace").strip()
    except OSError:
        return ""


def main():
    pid = int(sys.argv[1]) if len(sys.argv) > 1 else os.getppid()
    print(f"Cadena de ancestros desde el PID {pid}:\n")
    nivel = 0
    while pid > 0:
        try:
            nombre, ppid = leer_stat(pid)
        except FileNotFoundError:
            print(f"El PID {pid} ya no existe")
            break
        cmd = leer_cmdline(pid) or f"[{nombre}]"
        print(f"{'  ' * nivel}PID {pid:<7} PPID {ppid:<7} {nombre:<15} {cmd[:60]}")
        pid = ppid  # el PPID del PID 1 es 0: ahí termina
        nivel += 1


if __name__ == "__main__":
    main()
