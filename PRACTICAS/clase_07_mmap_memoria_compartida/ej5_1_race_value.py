#!/usr/bin/env python3
"""
Ejercicio 5.1 (obligatorio): race condition con un Value compartido.
Ejecutalo varias veces y observá cómo cambia el resultado.
Uso: python3 ej5_1_race_value.py [N]   (default N=100000 incrementos por proceso)
"""
from multiprocessing import Process, Value
import sys


def incrementar(contador, n, nombre):
    """Incrementa el contador n veces (SIN lock: leer + sumar + escribir no es atómico)."""
    print(f"[{nombre}] Iniciando {n} incrementos...")
    for _ in range(n):
        contador.value += 1
    print(f"[{nombre}] Terminado")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100000

    # Crear valor compartido ('i' = int de C), arranca en 0
    contador = Value('i', 0)

    # Lanzar 4 procesos que incrementan
    procesos = []
    for i in range(4):
        p = Process(target=incrementar, args=(contador, n, f"P{i}"))
        p.start()
        procesos.append(p)

    for p in procesos:
        p.join()

    esperado = 4 * n
    print(f"\nEsperado: {esperado}")
    print(f"Obtenido: {contador.value}")
    print(f"Diferencia: {esperado - contador.value} (incrementos perdidos)")


if __name__ == "__main__":
    main()
