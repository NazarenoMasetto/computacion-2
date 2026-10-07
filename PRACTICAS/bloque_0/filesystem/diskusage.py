#!/usr/bin/env python3
"""Ejercicio 3.2 - Analizador de uso de disco (parecido a du).

Ejemplos:
    python3 diskusage.py /home/usuario --depth 1
    python3 diskusage.py . --top 5
    python3 diskusage.py . --depth 2 --exclude "node_modules,*.log"
    python3 diskusage.py . --no-human      (tamaños en bytes)
"""

import argparse
import fnmatch
import os
import sys


def legible(n: int) -> str:
    """Formato corto estilo du -h: 12K, 256M, 1.2G."""
    valor = float(n)
    for unidad in ("B", "K", "M", "G", "T"):
        if valor < 1024 or unidad == "T":
            if unidad == "B":
                return f"{int(valor)}B"
            return f"{valor:.1f}{unidad}" if valor < 10 else f"{valor:.0f}{unidad}"
        valor /= 1024
    return f"{n}B"


def excluido(nombre: str, patrones: list[str]) -> bool:
    return any(fnmatch.fnmatch(nombre, p) for p in patrones)


def calcular(ruta: str, patrones: list[str], profundidad: int, max_prof: int,
             salida: list[tuple[int, str]], todos: list[tuple[int, str]]) -> int:
    """Calcula el tamaño de 'ruta' recursivamente.

    - salida: entradas hasta max_prof (para el listado por profundidad)
    - todos: todas las entradas (para --top)
    """
    try:
        info = os.lstat(ruta)
    except OSError:
        return 0
    if not os.path.isdir(ruta) or os.path.islink(ruta):
        tam = info.st_size
    else:
        tam = 0
        try:
            nombres = os.listdir(ruta)
        except PermissionError:
            print(f"Aviso: sin permiso para leer {ruta}", file=sys.stderr)
            nombres = []
        for nombre in nombres:
            if excluido(nombre, patrones):
                continue
            tam += calcular(os.path.join(ruta, nombre), patrones,
                            profundidad + 1, max_prof, salida, todos)
    if profundidad >= 1:
        todos.append((tam, ruta))
        if profundidad <= max_prof:
            salida.append((tam, ruta))
    return tam


def main() -> int:
    parser = argparse.ArgumentParser(description="Analizador de uso de disco")
    parser.add_argument("directorio")
    parser.add_argument("--depth", type=int, default=1, help="profundidad (default 1)")
    parser.add_argument("--top", type=int, default=None, help="mostrar los N más grandes")
    parser.add_argument("--exclude", default="",
                        help="patrones a excluir separados por coma (ej: 'node_modules,*.log')")
    parser.add_argument("--human", dest="human", action="store_true", default=True,
                        help="tamaños legibles (default)")
    parser.add_argument("--no-human", dest="human", action="store_false",
                        help="tamaños en bytes")
    args = parser.parse_args()

    if not os.path.isdir(args.directorio):
        print(f"Error: '{args.directorio}' no es un directorio o no existe", file=sys.stderr)
        return 1
    if args.depth < 1 or (args.top is not None and args.top < 1):
        print("Error: --depth y --top deben ser >= 1", file=sys.stderr)
        return 1

    patrones = [p.strip() for p in args.exclude.split(",") if p.strip()]
    fmt = legible if args.human else (lambda n: f"{n}")

    salida: list[tuple[int, str]] = []
    todos: list[tuple[int, str]] = []
    total = calcular(args.directorio, patrones, 0, args.depth, salida, todos)

    if args.top:
        print(f"Los {args.top} archivos/carpetas más grandes:")
        # Igual que en el ejemplo de la consigna, el top considera archivos y
        # carpetas de cualquier nivel (una carpeta incluye a su contenido).
        candidatos = sorted(todos, reverse=True)[:args.top]
        for i, (tam, ruta) in enumerate(candidatos, 1):
            print(f"  {i}. {ruta} ({fmt(tam)})")
    else:
        for tam, ruta in sorted(salida, reverse=True):
            print(f"{fmt(tam):<8}{ruta}")
        print("─" * 25)
        print(f"Total: {fmt(total)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
