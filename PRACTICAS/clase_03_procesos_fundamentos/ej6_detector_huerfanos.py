#!/usr/bin/env python3
"""Ejercicio adicional: detector de huérfanos.

Recorre /proc y lista los procesos cuyo PPID es 1, es decir, procesos
cuyo padre original murió y fueron "adoptados" por init/systemd
(o que fueron lanzados directamente por init, como los servicios).
Se excluye el propio PID 1.

Uso: python3 ej6_detector_huerfanos.py
Para generar un huérfano de prueba:  (sleep 120 &)
"""

import os


def leer_stat(pid):
    """Devuelve (nombre, estado, ppid) o None si el proceso ya no existe."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            datos = f.read()
    except (FileNotFoundError, ProcessLookupError):
        return None
    # El nombre está entre paréntesis y puede tener espacios
    nombre = datos[datos.index("(") + 1:datos.rindex(")")]
    resto = datos[datos.rindex(")") + 2:].split()
    return nombre, resto[0], int(resto[1])


def leer_cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().replace(b"\0", b" ").decode(errors="replace").strip()
    except OSError:
        return ""


def main():
    with open("/proc/1/comm") as f:
        init = f.read().strip()
    print(f"PID 1 en este sistema: {init}\n")

    huerfanos = []
    for entrada in os.listdir("/proc"):
        if not entrada.isdigit() or entrada == "1":
            continue
        info = leer_stat(entrada)
        if info and info[2] == 1:
            huerfanos.append((int(entrada), info[0], info[1]))

    print(f"{'PID':>7} {'EST':>3}  {'NOMBRE':<16} COMANDO")
    for pid, nombre, estado in sorted(huerfanos):
        cmd = leer_cmdline(pid) or f"[{nombre}]"
        print(f"{pid:>7} {estado:>3}  {nombre:<16} {cmd[:70]}")
    print(f"\nTotal de procesos con PPID 1: {len(huerfanos)}")


if __name__ == "__main__":
    main()
