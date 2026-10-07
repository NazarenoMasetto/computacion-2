#!/usr/bin/env python3
"""Ejercicio 3.3 - Sincronizador de directorios (un rsync simplificado).

Copia a destino los archivos nuevos o modificados de origen (por tamaño o
fecha de modificación), preservando fechas con shutil.copy2().

Ejemplos:
    python3 sync.py origen/ destino/
    python3 sync.py origen/ destino/ --dry-run
    python3 sync.py origen/ destino/ --delete
    python3 sync.py origen/ destino/ --exclude "*.tmp" --exclude ".git"
    python3 sync.py origen/ destino/ -y         (no pregunta confirmación)
"""

import argparse
import fnmatch
import os
import shutil
import sys
from datetime import datetime


def legible(n: int) -> str:
    valor = float(n)
    for unidad in ("B", "KB", "MB", "GB"):
        if valor < 1024:
            return f"{valor:.0f} {unidad}"
        valor /= 1024
    return f"{valor:.1f} TB"


def excluido(rel: str, patrones: list[str]) -> bool:
    """Un patrón puede matchear el path relativo o cualquier componente."""
    partes = rel.split(os.sep)
    return any(fnmatch.fnmatch(rel, p) or any(fnmatch.fnmatch(x, p) for x in partes)
               for p in patrones)


def archivos(base: str, patrones: list[str]) -> dict[str, os.stat_result]:
    """{ruta_relativa: stat} de todos los archivos regulares bajo base."""
    res = {}
    for raiz, dirs, nombres in os.walk(base, onerror=lambda e: print(
            f"Aviso: no se pudo leer {e.filename}", file=sys.stderr)):
        rel_raiz = os.path.relpath(raiz, base)
        # Podamos directorios excluidos para no recorrerlos
        dirs[:] = [d for d in dirs
                   if not excluido(os.path.normpath(os.path.join(rel_raiz, d)), patrones)]
        for n in nombres:
            rel = os.path.normpath(os.path.join(rel_raiz, n))
            ruta = os.path.join(raiz, n)
            if excluido(rel, patrones) or os.path.islink(ruta):
                continue  # symlinks se ignoran (versión simplificada)
            try:
                res[rel] = os.stat(ruta)
            except OSError:
                pass
    return res


def confirmar(pregunta: str) -> bool:
    try:
        return input(pregunta).strip().lower() in ("s", "si", "sí", "y")
    except EOFError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza origen -> destino")
    parser.add_argument("origen")
    parser.add_argument("destino")
    parser.add_argument("--dry-run", action="store_true", help="solo mostrar qué haría")
    parser.add_argument("--delete", action="store_true",
                        help="eliminar en destino lo que no existe en origen")
    parser.add_argument("--exclude", action="append", default=[], metavar="PATRON",
                        help="excluir archivos que coincidan (se puede repetir)")
    parser.add_argument("-y", "--yes", action="store_true", help="no pedir confirmación")
    args = parser.parse_args()

    if not os.path.isdir(args.origen):
        print(f"Error: el origen '{args.origen}' no es un directorio", file=sys.stderr)
        return 1
    if os.path.exists(args.destino) and not os.path.isdir(args.destino):
        print(f"Error: el destino '{args.destino}' existe y no es un directorio", file=sys.stderr)
        return 1
    if os.path.realpath(args.origen) == os.path.realpath(args.destino):
        print("Error: origen y destino son el mismo directorio", file=sys.stderr)
        return 1

    print("Analizando diferencias...\n")
    src = archivos(args.origen, args.exclude)
    dst = archivos(args.destino, args.exclude) if os.path.isdir(args.destino) else {}

    nuevos = sorted(r for r in src if r not in dst)
    modificados = sorted(r for r in src if r in dst and (
        src[r].st_size != dst[r].st_size or int(src[r].st_mtime) != int(dst[r].st_mtime)))
    eliminados = sorted(r for r in dst if r not in src)

    if not (nuevos or modificados or eliminados):
        print("Todo sincronizado, no hay cambios.")
        return 0

    print("Cambios detectados:")
    for r in nuevos:
        print(f"  NUEVO:      {r} ({legible(src[r].st_size)})")
    for r in modificados:
        fecha = datetime.fromtimestamp(src[r].st_mtime).strftime("%Y-%m-%d")
        print(f"  MODIFICADO: {r} (cambiado {fecha})")
    for r in eliminados:
        accion = "" if args.delete else " [se conserva, usar --delete]"
        print(f"  ELIMINADO:  {r} (existe en destino pero no en origen){accion}")
    print(f"\nResumen: {len(nuevos)} nuevos, {len(modificados)} modificados, "
          f"{len(eliminados)} eliminados")

    if args.dry_run:
        print("\n[dry-run] No se realizó ningún cambio.")
        return 0
    if not args.yes and not confirmar("\n¿Proceder con la sincronización? [s/N] "):
        print("Cancelado.")
        return 0
    print()

    errores = 0
    for r, verbo in [(r, "Copiando") for r in nuevos] + [(r, "Actualizando") for r in modificados]:
        print(f"{verbo} {r}...", end=" ")
        try:
            destino = os.path.join(args.destino, r)
            os.makedirs(os.path.dirname(destino) or ".", exist_ok=True)
            shutil.copy2(os.path.join(args.origen, r), destino)  # preserva mtime
            print("OK")
        except OSError as e:
            print(f"ERROR ({e.strerror})")
            errores += 1

    if args.delete:
        for r in eliminados:
            print(f"Eliminando {r}...", end=" ")
            try:
                os.remove(os.path.join(args.destino, r))
                print("OK")
            except OSError as e:
                print(f"ERROR ({e.strerror})")
                errores += 1
        # Borramos directorios que quedaron vacíos y no existen en origen
        for raiz, _dirs, _arch in os.walk(args.destino, topdown=False):
            rel = os.path.relpath(raiz, args.destino)
            if rel != "." and not os.path.isdir(os.path.join(args.origen, rel)):
                try:
                    os.rmdir(raiz)
                except OSError:
                    pass  # no está vacío (p. ej. por excluidos), lo dejamos

    print("Completado." if not errores else f"Completado con {errores} errores.")
    return 0 if not errores else 1


if __name__ == "__main__":
    sys.exit(main())
