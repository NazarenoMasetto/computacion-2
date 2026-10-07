#!/usr/bin/env python3
"""Adicional: pool manual de workers solo con fork.

El padre mantiene como máximo N hijos vivos; cada hijo procesa UNA tarea y
termina. Cuando uno termina, el padre lanza otro con la siguiente tarea.
Uso: python3 adicional_pool_manual.py [N]
"""
import os
import random
import sys
import time


def procesar(tarea):
    """Trabajo de ejemplo: duerme un rato y devuelve tarea % 256 como código."""
    time.sleep(random.uniform(0.2, 0.8))
    resultado = tarea * tarea
    print(f"  [hijo {os.getpid()}] tarea {tarea} -> {resultado}", flush=True)
    return resultado % 256  # el código de salida solo tiene 8 bits


def main(n_workers=3):
    tareas = list(range(1, 11))
    activos = {}  # pid -> tarea

    while tareas or activos:
        # Lanzar hijos mientras haya lugar y tareas pendientes
        while tareas and len(activos) < n_workers:
            tarea = tareas.pop(0)
            pid = os.fork()
            if pid == 0:
                random.seed()
                os._exit(procesar(tarea))
            activos[pid] = tarea
            print(f"[padre] lancé PID {pid} con tarea {tarea} (activos: {len(activos)})", flush=True)

        # Esperar a que termine cualquiera
        pid, status = os.wait()
        tarea = activos.pop(pid)
        print(f"[padre] PID {pid} terminó tarea {tarea}, código {os.WEXITSTATUS(status)}", flush=True)

    print("Todas las tareas procesadas")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
