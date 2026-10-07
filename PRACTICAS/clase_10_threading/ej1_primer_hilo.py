#!/usr/bin/env python3
"""Ejercicio 1: lanzar 3 hilos que cuentan del 1 al 5 y esperar a que terminen."""
import threading
import time


def imprimir_numeros(nombre):
    """Imprime del 1 al 5 con una pausa de 0.2s."""
    for i in range(1, 6):
        print(f"[{nombre}] número: {i}")
        time.sleep(0.2)


if __name__ == "__main__":
    hilos = [threading.Thread(target=imprimir_numeros, args=(f"Hilo-{i}",))
             for i in range(1, 4)]

    for h in hilos:
        h.start()
    # join: el principal espera a cada hilo
    for h in hilos:
        h.join()

    print("Listo")
