#!/usr/bin/env python3
"""Tarea 2: guardar 5 registros (id, nota, nombre[20]) en un archivo mapeado con mmap."""
import mmap
import struct
import os

ARCHIVO = "/tmp/registros.bin"
# '=' -> sin padding de alineación: 4 (int) + 4 (float) + 20 (bytes) = 28 bytes
FORMATO = "=i f 20s"
TAM_REGISTRO = struct.calcsize(FORMATO)

ALUMNOS = [
    (1, 8.5, "Ana"),
    (2, 6.0, "Bruno"),
    (3, 9.75, "Carla"),
    (4, 4.0, "Diego"),
    (5, 7.25, "Emilia"),
]


def main():
    total = TAM_REGISTRO * len(ALUMNOS)
    print(f"Formato {FORMATO!r}: {TAM_REGISTRO} bytes por registro, {total} en total")

    with open(ARCHIVO, "wb") as f:
        f.write(b"\x00" * total)

    with open(ARCHIVO, "r+b") as f:
        with mmap.mmap(f.fileno(), total) as mm:
            # Escribir: struct rellena con \x00 los nombres de menos de 20 bytes
            for i, (id_, nota, nombre) in enumerate(ALUMNOS):
                struct.pack_into(FORMATO, mm, i * TAM_REGISTRO, id_, nota, nombre.encode())

            # Leer
            print("\nid | nota  | nombre")
            for i in range(len(ALUMNOS)):
                id_, nota, nombre = struct.unpack_from(FORMATO, mm, i * TAM_REGISTRO)
                nombre = nombre.rstrip(b"\x00").decode()
                print(f"{id_:2d} | {nota:5.2f} | {nombre}")

    os.unlink(ARCHIVO)


if __name__ == "__main__":
    main()
