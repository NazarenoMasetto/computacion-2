#!/usr/bin/env python3
"""Ej 3 parte A, punto 2: el recolector de CPython cierra el descriptor.

Uso:
    python3 ej3_gc_fd.py
"""
import gc
import os
import socket


def make():
    x = socket.socket()
    return x.fileno()      # al salir, x pierde su última referencia


def main():
    fd = make()
    gc.collect()
    try:
        os.fstat(fd)
        print(f'fd {fd} sigue abierto')
    except OSError as e:
        print(f'fd {fd} ya está cerrado: {e}')
        print('Lo cerró socket.__del__ al llegar el refcount a 0 (no hizo falta gc).')

    # Contraejemplo: si guardo la referencia, el fd sigue vivo
    guardados = [socket.socket()]
    fd2 = guardados[0].fileno()
    os.fstat(fd2)
    print(f'fd {fd2} guardado en una lista: sigue abierto')


if __name__ == '__main__':
    main()
