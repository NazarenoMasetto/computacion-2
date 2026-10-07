#!/usr/bin/env python3
"""
Adicional: mmap como caché de disco vs lectura normal.
Genera un archivo con datos aleatorios (default 10 MB) en un directorio temporal
y compara el tiempo de: read() de todo, read() secuencial por bloques, mmap secuencial
por bloques, y lecturas aleatorias (seek+read vs indexar el mmap).

Uso: python3 adicional_mmap_cache.py [MB]
"""
import hashlib
import mmap
import os
import random
import sys
import tempfile
import time

BLOQUE = 64 * 1024        # 64 KB por lectura
LECTURAS_AL_AZAR = 20000  # cantidad de accesos aleatorios de 16 bytes


def medir(nombre, funcion):
    inicio = time.perf_counter()
    resultado = funcion()
    print(f"  {nombre:<32} {time.perf_counter() - inicio:8.4f} s")
    return resultado


def leer_todo(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def leer_por_bloques(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while bloque := f.read(BLOQUE):
            h.update(bloque)
    return h.hexdigest()


def mmap_por_bloques(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        for i in range(0, len(mm), BLOQUE):
            h.update(mm[i:i + BLOQUE])
    return h.hexdigest()


def azar_seek_read(ruta, offsets):
    total = 0
    with open(ruta, "rb") as f:
        for off in offsets:
            f.seek(off)
            total += f.read(16)[0]
    return total


def azar_mmap(ruta, offsets):
    total = 0
    with open(ruta, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        for off in offsets:
            total += mm[off:off + 16][0]
    return total


def main():
    mb = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    tamaño = mb * 1024 * 1024

    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "grande.bin")
        print(f"Generando {mb} MB aleatorios en {ruta}...")
        with open(ruta, "wb") as f:
            for _ in range(mb):
                f.write(os.urandom(1024 * 1024))

        print("\nLectura secuencial completa (calcula SHA-256 para verificar que leen lo mismo):")
        h1 = medir("read() de todo de una", lambda: leer_todo(ruta))
        h2 = medir(f"read() en bloques de {BLOQUE // 1024} KB", lambda: leer_por_bloques(ruta))
        h3 = medir(f"mmap en bloques de {BLOQUE // 1024} KB", lambda: mmap_por_bloques(ruta))
        print(f"  Hashes iguales: {h1 == h2 == h3}")

        offsets = [random.randrange(0, tamaño - 16) for _ in range(LECTURAS_AL_AZAR)]
        print(f"\nAcceso aleatorio ({LECTURAS_AL_AZAR} lecturas de 16 bytes):")
        a = medir("seek() + read()", lambda: azar_seek_read(ruta, offsets))
        b = medir("mmap[offset:offset+16]", lambda: azar_mmap(ruta, offsets))
        print(f"  Resultados iguales: {a == b}")
        print("\n(Ojo: el archivo recién escrito ya está en la page cache del kernel,"
              " así que medimos sobre todo el costo de syscalls y copias, no del disco.)")


if __name__ == "__main__":
    main()
