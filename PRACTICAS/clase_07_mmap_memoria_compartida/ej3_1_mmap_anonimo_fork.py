#!/usr/bin/env python3
"""Ejercicio 3.1: padre e hijo se comunican vía mmap anónimo (heredado por fork)."""
import mmap
import os
import struct


def main():
    # Crear mmap anónimo (MAP_SHARED por defecto -> el hijo comparte las mismas páginas)
    mm = mmap.mmap(-1, 256)

    pid = os.fork()

    if pid == 0:
        # === HIJO ===
        print(f"[HIJO {os.getpid()}] Escribiendo datos...")

        # Escribir un entero
        struct.pack_into('i', mm, 0, 42)

        # Escribir un string: primero el largo, después los bytes
        mensaje = b"Hola desde el hijo!"
        struct.pack_into('i', mm, 4, len(mensaje))
        mm[8:8 + len(mensaje)] = mensaje

        print("[HIJO] Datos escritos, terminando", flush=True)
        os._exit(0)

    else:
        # === PADRE ===
        os.wait()  # esperar al hijo = sincronización (sabemos que ya escribió)
        print("[PADRE] Hijo terminó, leyendo datos...")

        numero = struct.unpack_from('i', mm, 0)[0]
        print(f"[PADRE] Número: {numero}")

        largo = struct.unpack_from('i', mm, 4)[0]
        mensaje = bytes(mm[8:8 + largo]).decode()
        print(f"[PADRE] Mensaje: {mensaje}")

        mm.close()


if __name__ == "__main__":
    main()
