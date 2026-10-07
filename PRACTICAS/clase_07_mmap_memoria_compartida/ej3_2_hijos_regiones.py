#!/usr/bin/env python3
"""Ejercicio 3.2: varios hijos escriben en regiones separadas de un mmap anónimo."""
import mmap
import os
import struct

NUM_HIJOS = 4
TAMAÑO_POR_HIJO = 64
TAMAÑO_TOTAL = NUM_HIJOS * TAMAÑO_POR_HIJO


def main():
    mm = mmap.mmap(-1, TAMAÑO_TOTAL)

    hijos = []
    for i in range(NUM_HIJOS):
        pid = os.fork()
        if pid == 0:
            # Hijo: escribe SOLO en su región -> no pisa a nadie, no hace falta lock
            offset = i * TAMAÑO_POR_HIJO

            struct.pack_into('i', mm, offset, i)                # ID del hijo
            struct.pack_into('i', mm, offset + 4, os.getpid())  # PID

            msg = f"Hijo {i} (PID {os.getpid()})".encode()
            mm[offset + 8:offset + 8 + len(msg)] = msg

            os._exit(0)
        else:
            hijos.append(pid)

    # Padre espera a todos
    for pid in hijos:
        os.waitpid(pid, 0)

    # Leer resultados
    print("=== Datos escritos por los hijos ===")
    for i in range(NUM_HIJOS):
        offset = i * TAMAÑO_POR_HIJO
        hijo_id = struct.unpack_from('i', mm, offset)[0]
        hijo_pid = struct.unpack_from('i', mm, offset + 4)[0]
        msg = bytes(mm[offset + 8:offset + TAMAÑO_POR_HIJO]).rstrip(b'\x00').decode()
        print(f"  Región {i}: id={hijo_id}, pid={hijo_pid}, msg='{msg}'")

    mm.close()


if __name__ == "__main__":
    main()
