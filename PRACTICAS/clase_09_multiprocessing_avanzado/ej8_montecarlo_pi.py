#!/usr/bin/env python3
"""
Adicional: estimar pi con Monte Carlo en paralelo con Pool.

Uso: python3 ej8_montecarlo_pi.py [total_puntos] [workers]
"""
from multiprocessing import Pool
import math
import os
import random
import sys
import time


def contar_dentro(args):
    """Genera n puntos en [0,1]x[0,1] y cuenta cuántos caen dentro del círculo unitario."""
    n, semilla = args
    rnd = random.Random(semilla)  # semilla distinta por tarea para no repetir puntos
    dentro = 0
    for _ in range(n):
        x, y = rnd.random(), rnd.random()
        if x * x + y * y <= 1.0:
            dentro += 1
    return dentro


def estimar_pi(total, workers):
    tareas = workers * 4
    por_tarea = total // tareas
    args = [(por_tarea, os.getpid() * 1000 + i) for i in range(tareas)]
    with Pool(workers) as pool:
        dentro = sum(pool.map(contar_dentro, args))
    return 4 * dentro / (por_tarea * tareas)


if __name__ == "__main__":
    total = int(sys.argv[1]) if len(sys.argv) > 1 else 4_000_000
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else os.cpu_count()

    inicio = time.time()
    pi_seq = 4 * contar_dentro((total, 1)) / total
    t_seq = time.time() - inicio

    inicio = time.time()
    pi_par = estimar_pi(total, workers)
    t_par = time.time() - inicio

    print(f"Puntos: {total:,}")
    print(f"Secuencial:        pi ~ {pi_seq:.6f}  error={abs(pi_seq - math.pi):.6f}  {t_seq:.2f}s")
    print(f"Pool({workers}) paralelo: pi ~ {pi_par:.6f}  error={abs(pi_par - math.pi):.6f}  {t_par:.2f}s")
    print(f"Speedup: {t_seq / t_par:.2f}x")
