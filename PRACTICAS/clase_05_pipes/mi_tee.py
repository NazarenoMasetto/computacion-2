#!/usr/bin/env python3
"""Adicional: tee casero. Copia stdin a stdout y a uno o más archivos.

Uso: comando | python3 mi_tee.py [-a] archivo [archivo ...]
     -a  agrega al final en vez de truncar
"""
import sys


def main():
    args = sys.argv[1:]
    modo = "wb"
    if args and args[0] == "-a":
        modo = "ab"
        args = args[1:]

    archivos = [open(nombre, modo) for nombre in args]
    entrada = sys.stdin.buffer   # trabajamos en bytes: sirve para cualquier dato
    salida = sys.stdout.buffer
    try:
        while True:
            bloque = entrada.read1(65536)  # read1 devuelve lo disponible, sin esperar a llenar
            if not bloque:  # EOF
                break
            for f in archivos:
                f.write(bloque)
            if salida is not None:
                try:
                    salida.write(bloque)
                    salida.flush()
                except BrokenPipeError:
                    # Se cerró stdout: seguimos guardando en los archivos igual
                    salida = None
    finally:
        for f in archivos:
            f.close()


if __name__ == "__main__":
    main()
