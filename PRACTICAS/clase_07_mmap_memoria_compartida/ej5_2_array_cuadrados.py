#!/usr/bin/env python3
"""Ejercicio 5.2 (obligatorio): cálculo paralelo de cuadrados en un Array compartido."""
from multiprocessing import Process, Array
import time

TAMAÑO = 1000
NUM_PROCESOS = 4


def calcular_rango(resultado, inicio, fin):
    """Calcula el cuadrado de cada número en el rango (cada proceso toca solo su parte)."""
    for i in range(inicio, fin):
        resultado[i] = i * i


def main():
    # Array compartido de 1000 enteros (arranca en ceros)
    resultado = Array('i', TAMAÑO)

    # Dividir en 4 procesos; el último se lleva el resto si no divide exacto
    chunk = TAMAÑO // NUM_PROCESOS

    inicio = time.time()

    procesos = []
    for i in range(NUM_PROCESOS):
        ini = i * chunk
        fin = (i + 1) * chunk if i < NUM_PROCESOS - 1 else TAMAÑO
        p = Process(target=calcular_rango, args=(resultado, ini, fin))
        p.start()
        procesos.append(p)

    for p in procesos:
        p.join()

    duracion = time.time() - inicio

    # Verificar
    print(f"Cálculo completado en {duracion:.4f}s")
    print(f"resultado[0] = {resultado[0]}")      # 0
    print(f"resultado[10] = {resultado[10]}")    # 100
    print(f"resultado[99] = {resultado[99]}")    # 9801
    print(f"resultado[999] = {resultado[999]}")  # 998001

    # Verificar que todos son correctos
    errores = sum(1 for i in range(TAMAÑO) if resultado[i] != i * i)
    print(f"Errores: {errores}")


if __name__ == "__main__":
    main()
