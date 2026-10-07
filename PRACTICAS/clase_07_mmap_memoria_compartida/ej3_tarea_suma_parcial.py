#!/usr/bin/env python3
"""
Tarea 3: cada hijo suma un rango (hijo 0: 1-25, hijo 1: 26-50, ...) y deja el resultado
en su región del mmap; el padre junta las sumas parciales.

Uso: python3 ej3_tarea_suma_parcial.py [num_hijos] [por_hijo]   (default 4 y 25 -> 1..100)
"""
import mmap
import os
import struct
import sys

TAMAÑO_POR_HIJO = 16  # q (8 bytes) para la suma + i (4) para el id, sobra lugar
FORMATO = "q i"       # 'q' = entero de 64 bits, por si los rangos son grandes


def main():
    num_hijos = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    por_hijo = int(sys.argv[2]) if len(sys.argv) > 2 else 25

    mm = mmap.mmap(-1, num_hijos * TAMAÑO_POR_HIJO)

    hijos = []
    for i in range(num_hijos):
        inicio = i * por_hijo + 1
        fin = (i + 1) * por_hijo
        pid = os.fork()
        if pid == 0:
            parcial = sum(range(inicio, fin + 1))
            struct.pack_into(FORMATO, mm, i * TAMAÑO_POR_HIJO, parcial, i)
            print(f"[Hijo {i} PID {os.getpid()}] suma {inicio}..{fin} = {parcial}", flush=True)
            os._exit(0)
        hijos.append(pid)

    for pid in hijos:
        os.waitpid(pid, 0)

    total = 0
    for i in range(num_hijos):
        parcial, hijo_id = struct.unpack_from(FORMATO, mm, i * TAMAÑO_POR_HIJO)
        print(f"[PADRE] Región {i}: hijo {hijo_id} -> {parcial}")
        total += parcial
    mm.close()

    n = num_hijos * por_hijo
    esperado = n * (n + 1) // 2  # fórmula de Gauss
    print(f"[PADRE] Suma total 1..{n} = {total} (esperado {esperado}) -> "
          f"{'OK' if total == esperado else 'ERROR'}")


if __name__ == "__main__":
    main()
