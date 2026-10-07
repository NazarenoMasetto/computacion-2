#!/usr/bin/env python3
"""Ejercicio 1: explorar los métodos de Pool (map, map_async, imap, imap_unordered, starmap, apply_async).

Uso: python3 ej1_metodos_pool.py [dur_min] [dur_max]
Cambiando el rango de duraciones se ve cómo varía el orden en imap vs imap_unordered.
Con dur_min == dur_max (duración constante) el orden de imap_unordered queda casi igual al de imap.
"""
from multiprocessing import Pool
import random
import sys
import time

# Rango de duración aleatoria de cada tarea (se puede cambiar por argumento)
DUR_MIN = 0.1
DUR_MAX = 1.0


def cuadrado(x):
    """Tarea con duración variable para apreciar las diferencias."""
    duracion = random.uniform(DUR_MIN, DUR_MAX)
    time.sleep(duracion)
    return x ** 2


def suma(a, b):
    return a + b


def configurar(dmin, dmax):
    """Inicializador del Pool: pasa el rango de duraciones a cada worker."""
    global DUR_MIN, DUR_MAX
    DUR_MIN, DUR_MAX = dmin, dmax


if __name__ == "__main__":
    if len(sys.argv) == 3:
        DUR_MIN, DUR_MAX = float(sys.argv[1]), float(sys.argv[2])
    print(f"Duración de cada tarea: entre {DUR_MIN} y {DUR_MAX} s")

    with Pool(4, initializer=configurar, initargs=(DUR_MIN, DUR_MAX)) as pool:
        # map: síncrono, ordenado, bloquea hasta tener todo
        print("== map ==")
        print(pool.map(cuadrado, range(8)))

        # map_async: igual pero asíncrono
        print("\n== map_async ==")
        async_result = pool.map_async(cuadrado, range(8))
        print(f"ready inmediatamente? {async_result.ready()}")
        print(f"resultados: {async_result.get()}")

        # imap: iterador lazy, mantiene orden
        print("\n== imap (mantiene orden) ==")
        t0 = time.time()
        for r in pool.imap(cuadrado, range(8)):
            print(f"  llegó: {r:3d}  (t={time.time() - t0:.2f}s)")

        # imap_unordered: lazy, sin orden (más rápido)
        print("\n== imap_unordered (orden de finalización) ==")
        t0 = time.time()
        for r in pool.imap_unordered(cuadrado, range(8)):
            print(f"  llegó: {r:3d}  (t={time.time() - t0:.2f}s)")

        # starmap: función con múltiples argumentos
        print("\n== starmap ==")
        print(pool.starmap(suma, [(1, 2), (3, 4), (5, 6)]))

        # apply_async: control fino sobre tareas individuales
        print("\n== apply_async ==")
        resultado = pool.apply_async(cuadrado, (10,))
        print(f"ready? {resultado.ready()}")
        print(f"resultado: {resultado.get()}")
