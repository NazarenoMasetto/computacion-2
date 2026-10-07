#!/usr/bin/env python3
"""Ejercicio 2: speedup de multiprocessing con tareas CPU-bound (secuencial vs Pool 1/2/4/8)."""
from multiprocessing import Pool
import math
import os
import time


def cpu_task(n):
    """Tarea CPU-intensive: sumar raíces cuadradas."""
    return sum(math.sqrt(i) for i in range(n))


N = 500_000
TAREAS = 8

if __name__ == "__main__":
    print(f"CPUs disponibles: {os.cpu_count()}")
    # Secuencial
    inicio = time.time()
    resultados = [cpu_task(N) for _ in range(TAREAS)]
    t_seq = time.time() - inicio

    filas = [("Secuencial", t_seq, 1.0)]
    # Con distintos números de workers
    for workers in [1, 2, 4, 8]:
        inicio = time.time()
        with Pool(workers) as pool:
            resultados = pool.map(cpu_task, [N] * TAREAS)
        t_par = time.time() - inicio
        filas.append((f"Pool({workers})", t_par, t_seq / t_par))

    # Tabla de resultados
    print(f"\n{'Modo':<12}{'Tiempo (s)':>12}{'Speedup':>10}")
    print("-" * 34)
    for modo, t, s in filas:
        print(f"{modo:<12}{t:>12.2f}{s:>9.2f}x")
