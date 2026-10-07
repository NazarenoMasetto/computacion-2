#!/usr/bin/env python3
"""Ejercicio 2.1: usar mmap como almacenamiento binario estructurado (enteros de 4 bytes)."""
import mmap
import struct
import os

ARCHIVO = "/tmp/numeros.bin"
NUM_ELEMENTOS = 10
TAMAÑO = NUM_ELEMENTOS * 4  # 4 bytes por entero


def main():
    # Crear archivo con tamaño fijo (mmap necesita que el archivo ya mida eso)
    with open(ARCHIVO, "wb") as f:
        f.write(b'\x00' * TAMAÑO)

    with open(ARCHIVO, "r+b") as f:
        mm = mmap.mmap(f.fileno(), TAMAÑO)

        # Escribir números
        print("Escribiendo números...")
        for i in range(NUM_ELEMENTOS):
            valor = (i + 1) * 100
            struct.pack_into('i', mm, i * 4, valor)
            print(f"  Posición {i}: {valor}")

        # Leer todos los números
        print("\nLeyendo números...")
        for i in range(NUM_ELEMENTOS):
            valor = struct.unpack_from('i', mm, i * 4)[0]
            print(f"  Posición {i}: {valor}")

        # Modificar uno
        struct.pack_into('i', mm, 3 * 4, 9999)
        print(f"\nPosición 3 modificada a: {struct.unpack_from('i', mm, 3 * 4)[0]}")

        mm.close()

    os.unlink(ARCHIVO)


if __name__ == "__main__":
    main()
