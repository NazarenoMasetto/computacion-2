#!/usr/bin/env python3
"""Ejercicio 3.4 - Decorador @validate_types.

Verifica en tiempo de ejecución que los argumentos y el valor de retorno
respeten las anotaciones de tipo. Soporta tipos simples (int, str...),
Any, Optional/Union (incluido X | Y) y genéricos como list[int] (en ese caso
solo se chequea el contenedor, no cada elemento).
"""

import inspect
import types
import typing
from functools import wraps
from typing import Any, Callable


def _nombre(tipo: Any) -> str:
    return getattr(tipo, "__name__", None) or str(tipo).replace("typing.", "")


def _cumple(valor: Any, tipo: Any) -> bool:
    """True si `valor` es compatible con la anotación `tipo`."""
    if tipo is Any or tipo is inspect.Parameter.empty:
        return True
    if tipo is None or tipo is type(None):
        return valor is None
    origen = typing.get_origin(tipo)
    if origen is typing.Union or origen is types.UnionType:
        return any(_cumple(valor, t) for t in typing.get_args(tipo))
    if origen is not None:          # list[int], dict[str, int], etc.
        return isinstance(valor, origen)
    if isinstance(tipo, type):
        return isinstance(valor, tipo)
    return True  # anotaciones raras (TypeVar, strings, etc.): no validamos


def validate_types(func: Callable) -> Callable:
    """Decorador que lanza TypeError si los tipos no coinciden con las anotaciones."""
    firma = inspect.signature(func)
    # get_type_hints resuelve anotaciones escritas como string
    anotaciones = typing.get_type_hints(func)
    retorno = anotaciones.pop("return", inspect.Parameter.empty)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ligados = firma.bind(*args, **kwargs)  # TypeError si faltan/sobran args
        ligados.apply_defaults()
        for nombre, valor in ligados.arguments.items():
            if nombre in anotaciones and not _cumple(valor, anotaciones[nombre]):
                raise TypeError(f"'{nombre}' debe ser {_nombre(anotaciones[nombre])}, "
                                f"recibido {type(valor).__name__}")
        resultado = func(*args, **kwargs)
        if not _cumple(resultado, retorno):
            raise TypeError(f"retorno debe ser {_nombre(retorno)}, "
                            f"recibido {type(resultado).__name__}")
        return resultado

    return wrapper


@validate_types
def procesar(nombre: str, edad: int, activo: bool = True) -> str:
    return f"{nombre} tiene {edad} años"


@validate_types
def sumar(a: int, b: int) -> int:
    return str(a + b)  # Error a propósito: retorna str pero declara int


@validate_types
def buscar(clave: str, por_defecto: int | None = None) -> list[str]:
    return [clave] * (por_defecto or 1)


if __name__ == "__main__":
    print(procesar("Ana", 25))
    print(procesar("Ana", 25, False))

    pruebas = [
        lambda: procesar("Ana", "25"),
        lambda: procesar(123, 25),
        lambda: sumar(1, 2),
        lambda: buscar("x", "dos"),
    ]
    for prueba in pruebas:
        try:
            prueba()
        except TypeError as e:
            print(f"TypeError: {e}")

    print(buscar("x"), buscar("y", 2))  # Optional acepta None o int
    # Ojo: bool es subclase de int en Python, así que procesar("Ana", True) pasa
