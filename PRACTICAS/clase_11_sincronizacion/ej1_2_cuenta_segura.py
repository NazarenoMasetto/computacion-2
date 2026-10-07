#!/usr/bin/env python3
"""Ejercicio 1.2: cuenta bancaria thread-safe con Lock.

Resuelve el TODO: reutiliza el test del 1.1 con CuentaSegura y verifica
que el saldo final coincide con el esperado en varias corridas.
"""
import threading
import time

from ej1_1_cuenta_insegura import CuentaInsegura, probar


class CuentaSegura:
    """Cuenta con Lock: la sección leer-modificar-escribir es exclusiva."""

    def __init__(self, saldo):
        self.saldo = saldo
        self.lock = threading.Lock()

    def depositar(self, cantidad):
        with self.lock:
            actual = self.saldo
            time.sleep(0.001)
            self.saldo = actual + cantidad

    def retirar(self, cantidad):
        with self.lock:
            actual = self.saldo
            time.sleep(0.001)
            if actual >= cantidad:
                self.saldo = actual - cantidad
                return True
            return False


if __name__ == "__main__":
    corridas = 3
    for clase in (CuentaInsegura, CuentaSegura):
        print(f"=== {clase.__name__} ===")
        bien = 0
        for i in range(corridas):
            esperado, obtenido = probar(clase)
            ok = esperado == obtenido
            bien += ok
            print(f"  corrida {i + 1}: esperado={esperado} obtenido={obtenido} "
                  f"{'OK' if ok else 'MAL'}")
        print(f"  {bien}/{corridas} corridas correctas\n")

    # Verificación automática: la segura tiene que dar siempre bien
    esperado, obtenido = probar(CuentaSegura)
    assert esperado == obtenido, "CuentaSegura falló!"
    print("Verificación: CuentaSegura mantiene el saldo correcto.")
