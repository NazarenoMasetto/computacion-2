#!/usr/bin/env python3
"""Ejercicio 4.4 - Descriptor validador Positivo.

Un descriptor es una clase con __get__/__set__ que se pone como atributo de
clase; Python lo llama cada vez que se lee o asigna ese atributo en una
instancia. Acá validamos que el valor sea un número >= 0 (el 0 se permite
porque la consigna usa default=0).
"""

from numbers import Real
from typing import Any


class Positivo:
    """Atributo numérico que no puede ser negativo."""

    _SIN_DEFAULT = object()

    def __init__(self, default: Any = _SIN_DEFAULT) -> None:
        self.default = default
        if default is not Positivo._SIN_DEFAULT:
            self._validar(default)

    def __set_name__(self, owner: type, nombre: str) -> None:
        # Python nos avisa el nombre del atributo (ej: 'saldo')
        self.nombre = nombre
        self.privado = f"_{nombre}"

    def __get__(self, instancia: Any, owner: type | None = None) -> Any:
        if instancia is None:
            return self  # acceso desde la clase: Cuenta.saldo
        try:
            return getattr(instancia, self.privado)
        except AttributeError:
            if self.default is Positivo._SIN_DEFAULT:
                raise AttributeError(f"'{self.nombre}' no tiene valor asignado") from None
            return self.default

    def __set__(self, instancia: Any, valor: Any) -> None:
        self._validar(valor)
        setattr(instancia, self.privado, valor)

    def _validar(self, valor: Any) -> None:
        nombre = getattr(self, "nombre", "valor")
        if isinstance(valor, bool) or not isinstance(valor, Real):
            raise TypeError(f"{nombre} debe ser un número, recibido {type(valor).__name__}")
        if valor < 0:
            raise ValueError(f"{nombre} debe ser positivo")


class Cuenta:
    saldo = Positivo()
    limite = Positivo(default=0)

    def __init__(self, saldo, limite=1000):
        self.saldo = saldo
        self.limite = limite


if __name__ == "__main__":
    c = Cuenta(100, 500)
    print(c.saldo)   # 100
    print(c.limite)  # 500

    c.saldo = 200
    print(c.saldo)   # 200

    for valor in (-50, "mucho"):
        try:
            c.saldo = valor
        except (ValueError, TypeError) as e:
            print(f"{type(e).__name__}: {e}")

    try:
        Cuenta(-1)
    except ValueError as e:
        print(f"En el constructor también valida: {e}")

    # Cada instancia guarda su propio valor
    otra = Cuenta(5)
    print(c.saldo, otra.saldo, otra.limite)

    # El default se usa si nunca se asignó
    class Simple:
        limite = Positivo(default=0)
    print("Default:", Simple().limite)
