#!/usr/bin/env python3
"""Ejercicio 5: race condition en retiros bancarios y su corrección con Lock."""
import threading
import time

lock = threading.Lock()
saldo_inseguro = 1000
saldo_seguro = 1000


def retirar_inseguro(monto):
    """Chequea y descuenta SIN lock: entre el if y la resta otro hilo puede colarse."""
    global saldo_inseguro
    if saldo_inseguro >= monto:
        time.sleep(0.001)  # simular procesamiento
        saldo_inseguro -= monto
        print(f"[inseguro] Retiro de ${monto} exitoso. Saldo: ${saldo_inseguro}")
    else:
        print(f"[inseguro] Saldo insuficiente para retirar ${monto}")


def retirar_seguro(monto):
    """Chequeo + descuento dentro de la misma sección crítica."""
    global saldo_seguro
    with lock:
        if saldo_seguro >= monto:
            time.sleep(0.001)
            saldo_seguro -= monto
            print(f"[seguro] Retiro de ${monto} OK. Saldo: ${saldo_seguro}")
        else:
            print(f"[seguro] Saldo insuficiente para ${monto}. Saldo: ${saldo_seguro}")


def lanzar(funcion, cantidad=10, monto=200):
    hilos = [threading.Thread(target=funcion, args=(monto,)) for _ in range(cantidad)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()


if __name__ == "__main__":
    print("== Versión CON race condition ==")
    lanzar(retirar_inseguro)
    print(f"Saldo inseguro final: ${saldo_inseguro} (puede ser negativo)\n")

    print("== Versión CORREGIDA con Lock ==")
    lanzar(retirar_seguro)
    print(f"Saldo seguro final: ${saldo_seguro}")
    assert saldo_seguro == 0
