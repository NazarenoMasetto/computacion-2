from functools import wraps
from datetime import datetime


def log_llamada(funcion):
    @wraps(funcion)
    def wrapper(*args, **kwargs):
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        argumentos = [repr(arg) for arg in args]
        argumentos.extend(f"{k}={v!r}" for k, v in kwargs.items())
        argumentos_texto = ", ".join(argumentos)

        print(f"[{ahora}] Llamando a {funcion.__name__}({argumentos_texto})")
        resultado = funcion(*args, **kwargs)
        print(f"[{ahora}] {funcion.__name__} retornó {resultado!r}")
        return resultado

    return wrapper


@log_llamada
def sumar(a, b):
    return a + b


@log_llamada
def saludar(nombre, entusiasta=False):
    sufijo = "!" if entusiasta else "."
    return f"Hola, {nombre}{sufijo}"


if __name__ == "__main__":
    sumar(3, 5)
    saludar("Ana", entusiasta=True)