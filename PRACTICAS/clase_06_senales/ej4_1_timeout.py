#!/usr/bin/env python3
"""Ejercicio 4.1: decorador de timeout usando SIGALRM."""
import signal
import time


class Timeout(Exception):
    pass


def timeout_handler(sig, frame):
    # Levantar una excepción desde el handler corta la función que se estaba ejecutando
    raise Timeout("Operación excedió el tiempo límite")


def con_timeout(segundos):
    """Decorador para agregar timeout a una función."""
    def decorador(func):
        def wrapper(*args, **kwargs):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(segundos)
            try:
                return func(*args, **kwargs)
            finally:
                # Siempre cancelar la alarma y restaurar el handler anterior
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorador


@con_timeout(3)
def operacion_lenta():
    print("Iniciando operación...")
    time.sleep(5)
    return "Completado"


@con_timeout(3)
def operacion_rapida():
    print("Iniciando operación...")
    time.sleep(1)
    return "Completado"


def main():
    print("=== Operación rápida ===")
    try:
        resultado = operacion_rapida()
        print(f"Resultado: {resultado}")
    except Timeout as e:
        print(f"Timeout: {e}")

    print("\n=== Operación lenta ===")
    try:
        resultado = operacion_lenta()
        print(f"Resultado: {resultado}")
    except Timeout as e:
        print(f"Timeout: {e}")


if __name__ == "__main__":
    main()
