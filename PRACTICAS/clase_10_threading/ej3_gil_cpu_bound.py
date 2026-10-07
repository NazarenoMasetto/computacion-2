#!/usr/bin/env python3
"""
Ejercicio 3: el GIL en acción. Misma carga CPU-bound (4 tareas) ejecutada
secuencial, con 2 threads, con 4 threads y con 4 procesos.

Uso: python3 ej3_gil_cpu_bound.py [N]
"""
import math
import multiprocessing
import sys
import threading
import time

TAREAS = 4


def cpu_task(n):
    return sum(math.sqrt(i) for i in range(n))


def correr_threads(n, cantidad_hilos):
    """Reparte las TAREAS entre 'cantidad_hilos' threads."""
    def trabajo(k):
        for _ in range(k):
            cpu_task(n)
    por_hilo = TAREAS // cantidad_hilos
    hilos = [threading.Thread(target=trabajo, args=(por_hilo,)) for _ in range(cantidad_hilos)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()


def correr_procesos(n):
    procs = [multiprocessing.Process(target=cpu_task, args=(n,)) for _ in range(TAREAS)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()


def medir(nombre, funcion, *args):
    inicio = time.perf_counter()
    funcion(*args)
    t = time.perf_counter() - inicio
    print(f"{nombre:<12} {t:.2f}s")
    return t


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 2_000_000
    gil = sys._is_gil_enabled() if hasattr(sys, "_is_gil_enabled") else True
    print(f"{TAREAS} tareas de cpu_task({N:,}) - GIL activo: {gil}\n")

    t_seq = medir("Secuencial", lambda: [cpu_task(N) for _ in range(TAREAS)])
    t_2 = medir("2 threads", correr_threads, N, 2)
    t_4 = medir("4 threads", correr_threads, N, 4)
    t_p = medir("4 procesos", correr_procesos, N)

    print(f"\nSpeedup 2 threads: {t_seq / t_2:.2f}x | 4 threads: {t_seq / t_4:.2f}x"
          f" | 4 procesos: {t_seq / t_p:.2f}x")
