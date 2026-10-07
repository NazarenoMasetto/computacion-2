#!/usr/bin/env python3
"""Ejercicio 2: 5 procesos que duermen entre 0.5 y 2 s; se mide el tiempo total."""
import multiprocessing
import os
import random
import time


def worker(numero, duracion):
    """Simula trabajo durmiendo `duracion` segundos."""
    print(f"[Worker {numero}] PID={os.getpid()} duermo {duracion:.2f}s", flush=True)
    time.sleep(duracion)
    print(f"[Worker {numero}] listo", flush=True)


def main(n=5):
    # Sorteo las duraciones en el padre así puedo compararlas con el tiempo total
    duraciones = [random.uniform(0.5, 2) for _ in range(n)]

    inicio = time.perf_counter()
    procesos = [multiprocessing.Process(target=worker, args=(i, d)) for i, d in enumerate(duraciones)]
    for p in procesos:
        p.start()
    for p in procesos:
        p.join()
    total = time.perf_counter() - inicio

    print(f"\nSuma de las duraciones (secuencial): {sum(duraciones):.2f} s")
    print(f"Máxima duración: {max(duraciones):.2f} s")
    print(f"Tiempo total en paralelo: {total:.2f} s")


if __name__ == "__main__":
    main()
