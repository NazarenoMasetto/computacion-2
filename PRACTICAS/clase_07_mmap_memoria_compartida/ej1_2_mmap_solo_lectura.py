#!/usr/bin/env python3
"""Ejercicio 1.2: mapear un archivo en modo solo lectura (correr antes ej1_1)."""
import mmap

ARCHIVO = "/tmp/mmap_test.txt"


def main():
    # Asegurate de tener el archivo del ejercicio anterior
    with open(ARCHIVO, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        # Esto funciona:
        print(f"Contenido: {mm[:40]}")
        print(f"Tamaño: {mm.size()} bytes")

        # Esto lanza excepción:
        try:
            mm[0:4] = b"TEST"
        except TypeError as e:
            print(f"Error al escribir: {e}")

        mm.close()


if __name__ == "__main__":
    main()
