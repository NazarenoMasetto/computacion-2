import time
import random
from functools import wraps


def retry(max_attempts=3, delay=1, exceptions=(Exception,)):
    def decorador(funcion):
        @wraps(funcion)
        def wrapper(*args, **kwargs):
            ultimo_error = None

            for intento in range(1, max_attempts + 1):
                try:
                    return funcion(*args, **kwargs)
                except exceptions as error:
                    ultimo_error = error
                    if intento < max_attempts:
                        print(
                            f"Intento {intento}/{max_attempts} falló: {error}. "
                            f"Esperando {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        print(
                            f"Intento {intento}/{max_attempts} falló: {error}."
                        )

            raise ultimo_error

        return wrapper
    return decorador


@retry(max_attempts=3, delay=1, exceptions=(ConnectionError,))
def conectar_servidor():
    if random.random() < 0.7:
        raise ConnectionError("Servidor no disponible")
    return "Conectado exitosamente"


if __name__ == "__main__":
    try:
        resultado = conectar_servidor()
        print(resultado)
    except ConnectionError:
        print("Falló después de varios intentos.")