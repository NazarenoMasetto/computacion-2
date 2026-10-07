#!/usr/bin/env python3
"""Ejercicio 4.3 - Deduplicador de archivos.

Agrupa primero por tamaño (archivos de distinto tamaño no pueden ser iguales)
y solo calcula SHA-256 de los que coinciden en tamaño.

Ejemplos:
    python3 dedup.py ~/Downloads
    python3 dedup.py ~/Downloads --delete    (pregunta cuál mantener en cada grupo)
"""

import argparse
import hashlib
import os
import sys
from collections import defaultdict


def legible(n: float) -> str:
    for unidad in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unidad}" if unidad == "B" else f"{n:.1f} {unidad}"
        n /= 1024
    return f"{n:.1f} TB"


def sha256(ruta: str) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def buscar_duplicados(base: str) -> list[tuple[int, list[str]]]:
    """Devuelve [(tamaño, [rutas...]), ...] con grupos de 2 o más archivos iguales."""
    por_tamano: dict[int, list[str]] = defaultdict(list)
    vistos = set()  # (dispositivo, inodo) para no contar enlaces duros como copias
    for raiz, _dirs, archivos in os.walk(base, onerror=lambda e: None):
        for n in archivos:
            ruta = os.path.join(raiz, n)
            if os.path.islink(ruta):
                continue
            try:
                st = os.stat(ruta)
            except OSError:
                continue
            if (st.st_dev, st.st_ino) in vistos or st.st_size == 0:
                continue  # los vacíos no los consideramos duplicados útiles
            vistos.add((st.st_dev, st.st_ino))
            por_tamano[st.st_size].append(ruta)

    candidatos = [r for rutas in por_tamano.values() if len(rutas) > 1 for r in rutas]
    print(f"Calculando hashes de {len(candidatos)} archivos "
          f"(de {len(vistos)} totales)...\n")

    por_hash: dict[tuple[int, str], list[str]] = defaultdict(list)
    for tam, rutas in por_tamano.items():
        if len(rutas) < 2:
            continue
        for ruta in rutas:
            try:
                por_hash[(tam, sha256(ruta))].append(ruta)
            except OSError as e:
                print(f"Aviso: no se pudo leer {ruta}: {e.strerror}", file=sys.stderr)

    grupos = [(tam, sorted(rutas)) for (tam, _h), rutas in por_hash.items() if len(rutas) > 1]
    grupos.sort(key=lambda g: g[0] * (len(g[1]) - 1), reverse=True)
    return grupos


def main() -> int:
    parser = argparse.ArgumentParser(description="Encuentra archivos duplicados por contenido")
    parser.add_argument("directorio")
    parser.add_argument("--delete", action="store_true",
                        help="preguntar cuál conservar en cada grupo y borrar el resto")
    args = parser.parse_args()

    if not os.path.isdir(args.directorio):
        print(f"Error: '{args.directorio}' no es un directorio o no existe", file=sys.stderr)
        return 1

    grupos = buscar_duplicados(args.directorio)
    if not grupos:
        print("No se encontraron duplicados.")
        return 0

    print("Duplicados encontrados:\n")
    recuperable = 0
    for i, (tam, rutas) in enumerate(grupos, 1):
        print(f"Grupo {i} ({len(rutas)} copias, {legible(tam)} cada una):")
        for j, r in enumerate(rutas, 1):
            print(f"  [{j}] {os.path.relpath(r, args.directorio)}")
        print()
        recuperable += tam * (len(rutas) - 1)
    print(f"Espacio recuperable: {legible(recuperable)}")

    if args.delete:
        liberado = 0
        for i, (tam, rutas) in enumerate(grupos, 1):
            try:
                resp = input(f"\nGrupo {i}: ¿qué número conservar? (1-{len(rutas)}, "
                             f"Enter = saltear) ").strip()
            except EOFError:
                break
            if not resp:
                continue
            if not resp.isdigit() or not 1 <= int(resp) <= len(rutas):
                print("  Opción inválida, se saltea el grupo.")
                continue
            conservar = rutas[int(resp) - 1]
            for r in rutas:
                if r == conservar:
                    continue
                try:
                    os.remove(r)
                    liberado += tam
                    print(f"  Borrado: {r}")
                except OSError as e:
                    print(f"  Error al borrar {r}: {e.strerror}", file=sys.stderr)
        print(f"\nEspacio liberado: {legible(liberado)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
