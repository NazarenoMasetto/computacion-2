#!/usr/bin/env python3
"""Ejercicio 3.2: usar SIGCHLD para recoger hijos terminados sin bloquear al padre."""
import os
import signal
import time

hijos_activos = set()
resultados = {}


def sigchld_handler(sig, frame):
    """Recoger TODOS los hijos terminados (varios SIGCHLD pueden fusionarse en uno)."""
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break  # quedan hijos, pero ninguno terminó todavía
            hijos_activos.discard(pid)
            codigo = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
            resultados[pid] = codigo
            # Nota: print no es async-signal-safe, pero funciona en Python
            print(f"[SIGCHLD] Hijo {pid} terminó con código {codigo}", flush=True)
        except ChildProcessError:
            break  # no quedan hijos


def main():
    signal.signal(signal.SIGCHLD, sigchld_handler)

    # Crear 5 hijos con diferentes duraciones
    print("Creando 5 hijos...", flush=True)
    for i in range(5):
        pid = os.fork()
        if pid == 0:
            # Hijo
            duracion = (i + 1) * 0.5
            time.sleep(duracion)
            os._exit(i)
        else:
            hijos_activos.add(pid)
            print(f"Creado hijo {pid}, durará {(i + 1) * 0.5}s", flush=True)

    # El padre hace otras cosas mientras los hijos trabajan
    print("\n[PADRE] Trabajando mientras los hijos se ejecutan...", flush=True)
    for tick in range(10):
        print(f"[PADRE] Tick {tick}, hijos activos: {len(hijos_activos)}", flush=True)
        time.sleep(0.5)
        if not hijos_activos:
            break

    print(f"\n[PADRE] Todos terminaron. Resultados: {resultados}")


if __name__ == "__main__":
    main()
