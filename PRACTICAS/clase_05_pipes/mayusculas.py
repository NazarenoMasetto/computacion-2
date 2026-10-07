#!/usr/bin/env python3
"""Ejercicio 6.1: filtro Unix que convierte stdin a mayúsculas."""
import sys


def main():
    try:
        for linea in sys.stdin:
            sys.stdout.write(linea.upper())
        sys.stdout.flush()
    except BrokenPipeError:
        # Pasa si el siguiente comando (ej: head) cierra el pipe antes de tiempo
        sys.stderr.close()


if __name__ == "__main__":
    main()
