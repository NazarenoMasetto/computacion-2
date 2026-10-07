#!/usr/bin/env python3
"""
Adicional: procesar en paralelo todos los archivos de una carpeta.
Para cada archivo: cantidad de líneas, cantidad de apariciones de un patrón (regex) y hash SHA-256.

Uso: python3 ej10_procesador_archivos.py CARPETA [patron] [workers]
Ej:  python3 ej10_procesador_archivos.py /usr/lib/python3.13/json "def "
"""
from multiprocessing import Pool
import hashlib
import os
import re
import sys
import time


def procesar_archivo(args):
    """Devuelve un dict con las métricas de un archivo (o el error si no se pudo leer)."""
    ruta, patron = args
    try:
        with open(ruta, "rb") as f:
            datos = f.read()
    except OSError as e:
        return {"ruta": ruta, "error": str(e)}
    texto = datos.decode("utf-8", errors="replace")
    return {
        "ruta": ruta,
        "bytes": len(datos),
        "lineas": datos.count(b"\n"),
        "coincidencias": len(re.findall(patron, texto)),
        "sha256": hashlib.sha256(datos).hexdigest(),
    }


def listar_archivos(carpeta):
    """Recorre la carpeta recursivamente y devuelve las rutas de archivos regulares."""
    rutas = []
    for raiz, _, archivos in os.walk(carpeta):
        for nombre in archivos:
            ruta = os.path.join(raiz, nombre)
            if os.path.isfile(ruta) and not os.path.islink(ruta):
                rutas.append(ruta)
    return sorted(rutas)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Uso: {sys.argv[0]} CARPETA [patron] [workers]")
        sys.exit(1)
    carpeta = sys.argv[1]
    patron = sys.argv[2] if len(sys.argv) > 2 else "import"
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else os.cpu_count()

    rutas = listar_archivos(carpeta)
    print(f"{len(rutas)} archivos en {carpeta}, patrón={patron!r}, workers={workers}\n")

    inicio = time.time()
    with Pool(workers) as pool:
        # imap_unordered + chunksize: muchos archivos chicos, nos importa el total, no el orden
        resultados = list(pool.imap_unordered(procesar_archivo,
                                              [(r, patron) for r in rutas],
                                              chunksize=8))
    tiempo = time.time() - inicio

    resultados.sort(key=lambda r: r["ruta"])
    for r in resultados:
        if "error" in r:
            print(f"  ERROR {r['ruta']}: {r['error']}")
        else:
            print(f"  {os.path.relpath(r['ruta'], carpeta):40.40s} "
                  f"{r['lineas']:>7} líneas {r['coincidencias']:>5} match  {r['sha256'][:12]}")

    ok = [r for r in resultados if "error" not in r]
    print(f"\nTotal: {sum(r['lineas'] for r in ok):,} líneas, "
          f"{sum(r['coincidencias'] for r in ok):,} coincidencias, "
          f"{sum(r['bytes'] for r in ok):,} bytes en {tiempo:.2f}s")
