#!/usr/bin/env python3
"""Ejercicio 4: crear un zombie y después limpiarlo con wait().

Uso:
  python3 ej4_zombie.py            -> el padre NO hace wait (el hijo queda zombie 30 s)
  python3 ej4_zombie.py --wait     -> el padre hace wait y el zombie desaparece
  python3 ej4_zombie.py 5          -> igual que el primero pero durmiendo 5 s
"""
import os
import sys
import time


def estado(pid):
    """Devuelve el estado del proceso según /proc (Z = zombie)."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            # El 3er campo es el estado; el nombre va entre paréntesis
            return f.read().rsplit(")", 1)[1].split()[0]
    except FileNotFoundError:
        return "no existe"


def main():
    hacer_wait = "--wait" in sys.argv
    numeros = [a for a in sys.argv[1:] if a.isdigit()]
    espera = int(numeros[0]) if numeros else 30

    pid = os.fork()
    if pid == 0:
        print(f"[Hijo PID={os.getpid()}] termino inmediatamente", flush=True)
        os._exit(0)

    time.sleep(0.5)  # le doy tiempo al hijo para que termine
    print(f"[Padre PID={os.getpid()}] creé al hijo {pid}")
    print(f"Estado del hijo según /proc: {estado(pid)}")
    print("Mirá en otra terminal: ps aux | grep -E 'Z|defunct'")

    if hacer_wait:
        os.waitpid(pid, 0)
        print("Hijo recogido con wait().")
        print(f"Estado del hijo ahora: {estado(pid)}")
    print(f"Durmiendo {espera} s...", flush=True)
    time.sleep(espera)
    # Al terminar el padre, init/systemd adopta al zombie y lo recoge


if __name__ == "__main__":
    main()
