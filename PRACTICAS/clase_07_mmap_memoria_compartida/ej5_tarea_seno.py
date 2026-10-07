#!/usr/bin/env python3
"""
Tarea 5: Array('d') compartido con sin(i * 0.01) calculado por 4 procesos,
más un Value('d') donde cada proceso acumula sus resultados (bonus: race condition).

Uso: python3 ej5_tarea_seno.py [tamaño]   (default 100; probá con 200000 para ver la race)
"""
from multiprocessing import Process, Array, Value
import math
import sys

NUM_PROCESOS = 4


def calcular(arr, suma_sin_lock, suma_con_lock, inicio, fin):
    """Llena arr[inicio:fin] y acumula cada valor en las dos sumas compartidas."""
    for i in range(inicio, fin):
        valor = math.sin(i * 0.01)
        arr[i] = valor
        # Sin lock: leer y escribir son dos pasos -> se pueden perder sumas
        suma_sin_lock.value += valor
        # Con el lock que trae el Value: la operación completa es atómica
        with suma_con_lock.get_lock():
            suma_con_lock.value += valor


def main():
    tamaño = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    arr = Array('d', tamaño)
    suma_sin_lock = Value('d', 0.0)
    suma_con_lock = Value('d', 0.0)

    chunk = tamaño // NUM_PROCESOS
    procesos = []
    for i in range(NUM_PROCESOS):
        ini = i * chunk
        fin = (i + 1) * chunk if i < NUM_PROCESOS - 1 else tamaño
        p = Process(target=calcular, args=(arr, suma_sin_lock, suma_con_lock, ini, fin))
        p.start()
        procesos.append(p)

    for p in procesos:
        p.join()

    print("Primeros 20 resultados:")
    for i in range(min(20, tamaño)):
        print(f"  sin({i * 0.01:.2f}) = {arr[i]:.6f}")

    # Verificación contra el cálculo secuencial
    errores = sum(1 for i in range(tamaño) if arr[i] != math.sin(i * 0.01))
    esperado = sum(math.sin(i * 0.01) for i in range(tamaño))
    print(f"\nErrores en el array: {errores}")
    print(f"Suma esperada (secuencial): {esperado:.6f}")
    print(f"Suma con Value SIN lock:    {suma_sin_lock.value:.6f}  "
          f"(diferencia {esperado - suma_sin_lock.value:+.6f})")
    print(f"Suma con Value CON lock:    {suma_con_lock.value:.6f}  "
          f"(diferencia {esperado - suma_con_lock.value:+.6f})")
    # La suma de floats en distinto orden puede diferir en ~1e-12; eso NO es race condition
    if abs(esperado - suma_sin_lock.value) > 1e-6:
        print("-> La suma sin lock no coincide (se pisaron actualizaciones): race condition")
    else:
        print("-> Esta vez no se notó la race (con pocos elementos es raro); probá con más")


if __name__ == "__main__":
    main()
