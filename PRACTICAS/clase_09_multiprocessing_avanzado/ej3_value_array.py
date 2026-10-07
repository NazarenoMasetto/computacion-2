#!/usr/bin/env python3
"""Ejercicio 3: memoria compartida con Value (con get_lock) y Array.

Uso: python3 ej3_value_array.py [--sin-lock]
Con --sin-lock se muestra la race condition en el contador.
"""
from multiprocessing import Process, Value, Array
import sys


def incrementar(contador, n_veces, id):
    for _ in range(n_veces):
        # get_lock() previene race conditions (estudiado formalmente en clase 10)
        with contador.get_lock():
            contador.value += 1
    print(f"Worker {id} terminó sus {n_veces} incrementos")


def incrementar_sin_lock(contador, n_veces, id):
    """Versión rota a propósito: += no es atómico (leer, sumar, escribir)."""
    for _ in range(n_veces):
        contador.value += 1
    print(f"Worker {id} (sin lock) terminó sus {n_veces} incrementos")


def llenar_array(arr, valor_inicial, id):
    """Cada worker llena su segmento del array."""
    inicio = id * (len(arr) // 4)
    fin = inicio + (len(arr) // 4)
    for i in range(inicio, fin):
        arr[i] = valor_inicial + i


if __name__ == "__main__":
    sin_lock = "--sin-lock" in sys.argv
    funcion = incrementar_sin_lock if sin_lock else incrementar

    # Value compartido con auto-lock
    contador = Value('i', 0)
    procs = [Process(target=funcion, args=(contador, 10000, i)) for i in range(4)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()

    print(f"\nContador final: {contador.value} (esperado 40000)")
    if sin_lock:
        print(f"Se perdieron {40000 - contador.value} incrementos por la race condition")
    else:
        assert contador.value == 40000, "¡Race condition! Falta el lock"

    # Array compartido, particionado por worker (cada uno escribe su segmento)
    arr = Array('i', 100)
    procs = [Process(target=llenar_array, args=(arr, 1000, i)) for i in range(4)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()

    print(f"Array completo (primeros 10): {list(arr)[:10]}")
    print(f"Array completo (últimos 10): {list(arr)[-10:]}")
    assert list(arr) == [1000 + i for i in range(100)]
