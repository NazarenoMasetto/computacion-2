#!/usr/bin/env python3
"""
Adicional: merge sort paralelo.
La lista se divide en tantas partes como workers, cada parte se ordena en un proceso
(con merge sort secuencial) y después el padre hace los merges finales.
Se mide para varios tamaños para ver a partir de cuándo conviene paralelizar.

Uso: python3 ej9_merge_sort_paralelo.py [workers]
"""
from multiprocessing import Pool
import os
import random
import sys
import time


def merge(a, b):
    """Mezcla dos listas ordenadas."""
    resultado = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            resultado.append(a[i]); i += 1
        else:
            resultado.append(b[j]); j += 1
    resultado.extend(a[i:])
    resultado.extend(b[j:])
    return resultado


def merge_sort(lista):
    """Merge sort secuencial clásico (recursivo)."""
    if len(lista) <= 1:
        return lista
    medio = len(lista) // 2
    return merge(merge_sort(lista[:medio]), merge_sort(lista[medio:]))


def merge_sort_paralelo(lista, workers):
    """Divide en 'workers' partes, ordena cada una en un proceso y mergea en el padre."""
    tam = (len(lista) + workers - 1) // workers
    partes = [lista[i:i + tam] for i in range(0, len(lista), tam)]
    with Pool(workers) as pool:
        ordenadas = pool.map(merge_sort, partes)
    # Merges finales por pares (como un árbol)
    while len(ordenadas) > 1:
        siguientes = []
        for k in range(0, len(ordenadas), 2):
            if k + 1 < len(ordenadas):
                siguientes.append(merge(ordenadas[k], ordenadas[k + 1]))
            else:
                siguientes.append(ordenadas[k])
        ordenadas = siguientes
    return ordenadas[0] if ordenadas else []


if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else os.cpu_count()
    print(f"Workers: {workers}")
    print(f"{'Tamaño':>10}{'Secuencial':>13}{'Paralelo':>11}{'Speedup':>10}")
    for n in [1_000, 10_000, 50_000, 200_000, 500_000]:
        datos = [random.randint(0, 1_000_000) for _ in range(n)]

        t0 = time.time()
        sec = merge_sort(datos)
        t_seq = time.time() - t0

        t0 = time.time()
        par = merge_sort_paralelo(datos, workers)
        t_par = time.time() - t0

        assert sec == par == sorted(datos)
        print(f"{n:>10,}{t_seq:>12.3f}s{t_par:>10.3f}s{t_seq / t_par:>9.2f}x")
