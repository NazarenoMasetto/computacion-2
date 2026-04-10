import time
from contextlib import contextmanager


class Timer:
    def __init__(self, nombre=None):
        self.nombre = nombre
        self.inicio = None
        self.elapsed = 0

    def __enter__(self):
        self.inicio = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.elapsed = time.time() - self.inicio
        if self.nombre:
            print(f"[Timer] {self.nombre}: {self.elapsed:.3f}s")


@contextmanager
def timer_context(nombre=None):
    inicio = time.time()

    class Resultado:
        elapsed = 0

    resultado = Resultado()

    try:
        yield resultado
    finally:
        resultado.elapsed = time.time() - inicio
        if nombre:
            print(f"[Timer] {nombre}: {resultado.elapsed:.3f}s")


if __name__ == "__main__":
    with Timer("Prueba con clase") as t:
        time.sleep(1)

    print(f"Tiempo medido: {t.elapsed:.3f}s")

    with timer_context("Prueba con contextmanager") as t2:
        time.sleep(1)

    print(f"Tiempo medido: {t2.elapsed:.3f}s")