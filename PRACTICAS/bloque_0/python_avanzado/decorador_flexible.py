#!/usr/bin/env python3
"""Ejercicio 4.1 - Decorador flexible (con y sin paréntesis).

@mi_decorador, @mi_decorador() y @mi_decorador(verbose=True) funcionan igual.
El truco: si el primer argumento posicional es callable, nos usaron sin
paréntesis y ya podemos decorar; si no, devolvemos el decorador real.
Los parámetros son keyword-only para que no haya ambigüedad.
"""

import time
from functools import wraps
from typing import Any, Callable


def mi_decorador(func: Callable | None = None, *, verbose: bool = False) -> Callable:
    """Cuenta las llamadas a la función; con verbose=True también muestra args y tiempo."""

    def decorar(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            wrapper.llamadas += 1
            inicio = time.perf_counter()
            resultado = f(*args, **kwargs)
            if verbose:
                print(f"[verbose] {f.__name__}{args} {kwargs or ''} -> {resultado!r} "
                      f"({time.perf_counter() - inicio:.6f}s)")
            else:
                print(f"[mi_decorador] {f.__name__} llamada #{wrapper.llamadas}")
            return resultado

        wrapper.llamadas = 0
        return wrapper

    if func is None:
        return decorar          # se usó como @mi_decorador() o @mi_decorador(verbose=...)
    if callable(func):
        return decorar(func)    # se usó como @mi_decorador
    raise TypeError("mi_decorador solo acepta parámetros por nombre (ej: verbose=True)")


@mi_decorador
def funcion1():
    pass


@mi_decorador()
def funcion2():
    pass


@mi_decorador(verbose=True)
def funcion3(x=1):
    return x * 10


if __name__ == "__main__":
    funcion1()
    funcion1()
    funcion2()
    funcion3(4)
    print("funcion1 se llamó", funcion1.llamadas, "veces; nombre preservado:", funcion1.__name__)
    try:
        mi_decorador(True)
    except TypeError as e:
        print(f"Error esperado: {e}")
