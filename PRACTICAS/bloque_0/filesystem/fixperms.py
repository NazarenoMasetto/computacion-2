#!/usr/bin/env python3
"""Ejercicio 4.2 - Normalizador de permisos.

Recorre un directorio y deja los archivos regulares con --files, los
directorios con --dirs y los scripts (.sh/.py o con shebang) con --scripts.

Ejemplos:
    python3 fixperms.py proyecto/ --files 644 --dirs 755 --scripts 755
    python3 fixperms.py proyecto/ --dry-run
    python3 fixperms.py proyecto/ -y
"""

import argparse
import os
import stat
import sys

EXTENSIONES_SCRIPT = (".sh", ".py")


def modo_octal(texto: str) -> int:
    try:
        valor = int(texto, 8)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' no es un permiso octal válido (ej: 644)")
    if not 0 <= valor <= 0o7777:
        raise argparse.ArgumentTypeError(f"'{texto}' fuera de rango")
    return valor


def es_script(ruta: str) -> bool:
    """Es script si tiene extensión .sh/.py o empieza con '#!'."""
    if ruta.endswith(EXTENSIONES_SCRIPT):
        return True
    try:
        with open(ruta, "rb") as f:
            return f.read(2) == b"#!"
    except OSError:
        return False


def confirmar(pregunta: str) -> bool:
    try:
        return input(pregunta).strip().lower() in ("s", "si", "sí", "y")
    except EOFError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Normaliza permisos de un árbol de archivos")
    parser.add_argument("directorio")
    parser.add_argument("--files", type=modo_octal, default=0o644)
    parser.add_argument("--dirs", type=modo_octal, default=0o755)
    parser.add_argument("--scripts", type=modo_octal, default=0o755)
    parser.add_argument("--dry-run", action="store_true", help="solo mostrar los cambios")
    parser.add_argument("-y", "--yes", action="store_true", help="no pedir confirmación")
    parser.add_argument("-v", "--verbose", action="store_true", help="listar cada cambio")
    args = parser.parse_args()

    if not os.path.isdir(args.directorio):
        print(f"Error: '{args.directorio}' no es un directorio o no existe", file=sys.stderr)
        return 1

    cambios = {"archivos": [], "dirs": [], "scripts": []}
    total = 0
    for raiz, dirs, archivos in os.walk(args.directorio, onerror=lambda e: print(
            f"Aviso: no se pudo leer {e.filename}", file=sys.stderr)):
        for nombre in dirs + archivos:
            ruta = os.path.join(raiz, nombre)
            try:
                st = os.lstat(ruta)
            except OSError:
                continue
            if stat.S_ISLNK(st.st_mode):
                continue  # los permisos de un symlink no importan
            total += 1
            actual = stat.S_IMODE(st.st_mode)
            if stat.S_ISDIR(st.st_mode):
                categoria, deseado = "dirs", args.dirs
            elif stat.S_ISREG(st.st_mode):
                if es_script(ruta):
                    categoria, deseado = "scripts", args.scripts
                else:
                    categoria, deseado = "archivos", args.files
            else:
                continue  # dispositivos, fifos, etc. no se tocan
            if actual != deseado:
                cambios[categoria].append((ruta, actual, deseado))

    # La raíz también es un directorio a normalizar
    try:
        actual = stat.S_IMODE(os.stat(args.directorio).st_mode)
        if actual != args.dirs:
            cambios["dirs"].append((args.directorio, actual, args.dirs))
    except OSError:
        pass

    print(f"Analizando {total} archivos en {args.directorio}...\n")
    pendientes = [c for lista in cambios.values() for c in lista]
    if not pendientes:
        print("No hay cambios necesarios.")
        return 0

    print("Cambios necesarios:")
    print(f"  Archivos regulares (-> {args.files:o}): {len(cambios['archivos'])}")
    print(f"  Directorios (-> {args.dirs:o}): {len(cambios['dirs'])}")
    print(f"  Scripts .sh/.py ejecutables (-> {args.scripts:o}): {len(cambios['scripts'])}")
    if args.verbose or args.dry_run:
        for ruta, viejo, nuevo in pendientes:
            print(f"    {ruta}: {viejo:o} -> {nuevo:o}")

    if args.dry_run:
        print("\n[dry-run] No se aplicó nada.")
        return 0
    if not args.yes and not confirmar("\n¿Aplicar cambios? [s/N] "):
        print("Cancelado.")
        return 0

    print("Aplicando...", end=" ")
    errores = 0
    # Primero archivos, después directorios de abajo hacia arriba, para no
    # quitarnos permisos de un dir antes de tocar lo que tiene adentro.
    orden = cambios["archivos"] + cambios["scripts"] + sorted(
        cambios["dirs"], key=lambda c: c[0].count(os.sep), reverse=True)
    for ruta, _viejo, nuevo in orden:
        try:
            os.chmod(ruta, nuevo)
        except OSError as e:
            errores += 1
            print(f"\n  Error en {ruta}: {e.strerror}", file=sys.stderr)
    print("OK" if not errores else f"terminado con {errores} errores")
    return 0 if not errores else 1


if __name__ == "__main__":
    sys.exit(main())
