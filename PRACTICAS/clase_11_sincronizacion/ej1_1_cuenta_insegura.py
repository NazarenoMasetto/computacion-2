#!/usr/bin/env python3
"""Ejercicio 1.1: demostración de race condition en una cuenta bancaria."""
import random
import threading
import time


class CuentaInsegura:
    """Cuenta SIN sincronización: leer-modificar-escribir no es atómico."""

    def __init__(self, saldo):
        self.saldo = saldo

    def depositar(self, cantidad):
        actual = self.saldo
        time.sleep(0.001)  # Simula procesamiento (abre la ventana de la race)
        self.saldo = actual + cantidad

    def retirar(self, cantidad):
        actual = self.saldo
        time.sleep(0.001)
        if actual >= cantidad:
            self.saldo = actual - cantidad
            return True
        return False


def probar(clase_cuenta, num_threads=10, ops=100, semilla=None):
    """Corre operaciones al azar y devuelve (saldo_esperado, saldo_obtenido).

    Para poder comparar, cada thread lleva la cuenta de lo que efectivamente
    depositó y retiró; el saldo esperado sale de esos totales.
    """
    cuenta = clase_cuenta(1000)
    totales = {"depositos": 0, "retiros": 0}
    lock_totales = threading.Lock()  # solo protege el contador de control

    def operaciones_aleatorias(id_thread):
        rng = random.Random(None if semilla is None else semilla + id_thread)
        dep = ret = 0
        for _ in range(ops):
            if rng.choice([True, False]):
                cuenta.depositar(10)
                dep += 10
            elif cuenta.retirar(10):
                ret += 10
        with lock_totales:
            totales["depositos"] += dep
            totales["retiros"] += ret

    threads = [threading.Thread(target=operaciones_aleatorias, args=(i,))
               for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    esperado = 1000 + totales["depositos"] - totales["retiros"]
    return esperado, cuenta.saldo


if __name__ == "__main__":
    esperado, obtenido = probar(CuentaInsegura)
    print(f"Saldo esperado (según operaciones exitosas): {esperado}")
    print(f"Saldo obtenido: {obtenido}")
    if esperado != obtenido:
        print(f"-> RACE CONDITION: se 'perdieron' {esperado - obtenido} pesos")
    else:
        print("-> Esta vez coincidió (correlo de nuevo)")
