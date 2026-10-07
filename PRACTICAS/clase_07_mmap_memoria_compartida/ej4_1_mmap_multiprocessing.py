#!/usr/bin/env python3
"""Ejercicio 4.1: mmap sobre un archivo compartido entre procesos de multiprocessing."""
import mmap
import os
import struct
from multiprocessing import Process

# No podemos pasarle el objeto mmap a un Process (no se puede serializar),
# así que cada proceso abre el archivo y hace su propio mmap: como es
# MAP_SHARED sobre el mismo archivo, todos ven la misma memoria.
ARCHIVO = "/tmp/mmap_mp.bin"
TAMAÑO = 256


def escribir_en_mmap(archivo, offset, mensaje):
    """Cada proceso abre el archivo y escribe en su offset."""
    with open(archivo, "r+b") as f:
        mm = mmap.mmap(f.fileno(), TAMAÑO)
        encoded = mensaje.encode()
        struct.pack_into('i', mm, offset, len(encoded))
        mm[offset + 4:offset + 4 + len(encoded)] = encoded
        mm.close()


def main():
    with open(ARCHIVO, "wb") as f:
        f.write(b'\x00' * TAMAÑO)

    mensajes = [
        "Hola desde proceso 0",
        "Saludos del proceso 1",
        "Proceso 2 presente",
        "Proceso 3 reportando",
    ]

    procesos = []
    for i, msg in enumerate(mensajes):
        p = Process(target=escribir_en_mmap, args=(ARCHIVO, i * 64, msg))
        p.start()
        procesos.append(p)

    for p in procesos:
        p.join()

    # Leer resultados
    with open(ARCHIVO, "r+b") as f:
        mm = mmap.mmap(f.fileno(), TAMAÑO)
        print("=== Mensajes de los procesos ===")
        for i in range(4):
            offset = i * 64
            largo = struct.unpack_from('i', mm, offset)[0]
            if largo > 0:
                msg = bytes(mm[offset + 4:offset + 4 + largo]).decode()
                print(f"  Proceso {i}: {msg}")
        mm.close()

    os.unlink(ARCHIVO)


if __name__ == "__main__":
    main()
