#!/usr/bin/env python3
"""Ejercicio 3.2 - Context manager Transaction.

Guarda el estado de los atributos de un objeto al entrar y, si el bloque
termina con una excepción, lo restaura. Si termina bien, deja los cambios.
"""

import copy
from typing import Any


class Transaction:
    """Revierte los atributos de `obj` si el bloque with lanza una excepción."""

    def __init__(self, obj: Any, profunda: bool = True) -> None:
        self.obj = obj
        # Con copia profunda también se revierten cambios dentro de listas/dicts
        self._copiar = copy.deepcopy if profunda else copy.copy
        self._estado: dict[str, Any] = {}

    def _atributos(self) -> dict[str, Any]:
        """Atributos del objeto, tanto de __dict__ como de __slots__."""
        attrs = dict(vars(self.obj)) if hasattr(self.obj, "__dict__") else {}
        for clase in type(self.obj).__mro__:
            for nombre in getattr(clase, "__slots__", ()):
                if nombre not in ("__dict__", "__weakref__") and hasattr(self.obj, nombre):
                    attrs[nombre] = getattr(self.obj, nombre)
        return attrs

    def __enter__(self) -> Any:
        self._estado = self._copiar(self._atributos())
        return self.obj

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            # Borramos atributos nuevos y restauramos los originales
            for nombre in set(self._atributos()) - set(self._estado):
                delattr(self.obj, nombre)
            for nombre, valor in self._estado.items():
                setattr(self.obj, nombre, valor)
        return False  # la excepción sigue propagándose


class Cuenta:
    def __init__(self, saldo):
        self.saldo = saldo
        self.nombre = "Sin nombre"


if __name__ == "__main__":
    cuenta = Cuenta(1000)

    with Transaction(cuenta):
        cuenta.saldo -= 100
        cuenta.saldo -= 200
    print(cuenta.saldo)  # 700

    try:
        with Transaction(cuenta):
            cuenta.saldo -= 100
            cuenta.nombre = "Test"
            cuenta.extra = "atributo nuevo"
            raise ValueError("Error simulado")
    except ValueError:
        pass
    print(cuenta.saldo)                  # 700
    print(cuenta.nombre)                 # Sin nombre
    print(hasattr(cuenta, "extra"))      # False

    # Mutaciones internas también se revierten (copia profunda)
    cuenta.movimientos = [1, 2]
    try:
        with Transaction(cuenta):
            cuenta.movimientos.append(3)
            raise RuntimeError
    except RuntimeError:
        pass
    print(cuenta.movimientos)            # [1, 2]

    # Objetos con __slots__
    class Punto:
        __slots__ = ("x", "y")

        def __init__(self, x, y):
            self.x, self.y = x, y

    pt = Punto(1, 2)
    try:
        with Transaction(pt):
            pt.x = 99
            raise KeyError
    except KeyError:
        pass
    print(pt.x, pt.y)                    # 1 2
