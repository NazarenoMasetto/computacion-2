import os
from contextlib import contextmanager


@contextmanager
def archivo_temporal(nombre):
    archivo = open(nombre, "w+", encoding="utf-8")
    try:
        yield archivo
    finally:
        archivo.close()
        if os.path.exists(nombre):
            os.remove(nombre)


if __name__ == "__main__":
    with archivo_temporal("test.txt") as f:
        f.write("Datos de prueba\n")
        f.write("Más datos\n")
        f.seek(0)
        print(f.read())

    print("¿Existe el archivo después del with?:", os.path.exists("test.txt"))